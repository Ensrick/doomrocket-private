local mod = get_mod("doomrocket")

-- A transition blends the last displayed, corrected pose toward a moving pure
-- target. The helper uses this skeleton's zero-edge sampler, never the native
-- carrier's ASM. Ordinary same-owner transitions keep their native blends.
local OUTFIT = "units/warlock_bombardier/warlock_bombardier_3p"
local SPEED = "warlock_move_speed"
local AIM = "aim_target"
local BONE_COUNT = 138
local entries = {}
local startup_reports = {}

local function finite(value)
	return type(value) == "number" and value == value and math.abs(value) < math.huge
end

local function live(unit, world)
	return unit and Unit.alive(unit) and Unit.world(unit) == world
end

local function binding(owner, entry)
	return live(owner, entry.world) and live(entry.outfit, entry.world)
		and mod._warlock_outfits and mod._warlock_outfits[owner] == entry.outfit
		and Unit.get_data(entry.outfit, "warlock_animation_manifest_id") == entry.profile.manifest_id
end

local function diagnostic(entry, reason)
	entry.reported = entry.reported or {}
	if entry.reported[reason] then return end
	entry.reported[reason] = true
	local output = mod.warning or mod.echo
	if type(output) == "function" then
		pcall(output, mod, "Warlock animation sampler stopped: %s state=%s event=%s time=%s length=%s previous=%s dt=%s rate=%s expected=%s visible_time=%s visible_length=%s",
			reason, tostring(entry.state), tostring(entry.event), tostring(entry.observed_time), tostring(entry.observed_length),
			tostring(entry.previous_clock), tostring(entry.sample_dt), tostring(entry.sample_rate), tostring(entry.expected_clock),
			tostring(entry.observed_visible_time), tostring(entry.observed_visible_length))
	end
end

local function destroy(entry)
	local helper = entry.helper
	entry.helper = nil
	local ok = pcall(function()
		if helper and Unit.alive(helper) and Unit.world(helper) == entry.world then
			World.destroy_unit(entry.world, helper)
		end
	end)
	if not ok then diagnostic(entry, "sampler_cleanup_error") end
end

local function remove(owner, entry)
	entries[owner] = nil
	destroy(entry)
end

local function healthy(owner, entry)
	local alive = HEALTH_ALIVE and HEALTH_ALIVE[owner]
	if alive == true then entry.awaiting_health = false; return true end
	if alive ~= nil or not entry.awaiting_health then remove(owner, entry) end
	return false
end

local function usable(owner, entry)
	if not entry then return false end
	if not binding(owner, entry) then remove(owner, entry); return false end
	if not healthy(owner, entry) then return false end
	if not live(entry.helper, entry.world) then
		entry.blocked, entry.status = true, "missing_sampler"
		diagnostic(entry, "missing_sampler")
		return false
	end
	return true
end

local function fail(entry, reason)
	entry.blocked, entry.status = true, reason
	diagnostic(entry, reason)
	return false
end

local function vector(value, positive)
	if not Vector3.is_valid(value) or not finite(value.x) or not finite(value.y) or not finite(value.z)
		or (positive and (value.x <= 0 or value.y <= 0 or value.z <= 0)) then return end
	return { value.x, value.y, value.z }
end

local function quaternion(value)
	local x, y, z, w = Quaternion.to_elements(value)
	if not finite(x) or not finite(y) or not finite(z) or not finite(w) then return end
	local length = math.sqrt(x*x + y*y + z*z + w*w)
	if not finite(length) or length < 0.000001 then return end
	return { x/length, y/length, z/length, w/length }
end

local function aim(value)
	-- Native builds return a target matrix; the constraint setter also accepts
	-- vectors. Check every matrix axis/translation before passing the temporary
	-- directly to the setter, and never retain a native value across frames.
	local ok, position = pcall(vector, value)
	if ok and position then return Vector3(unpack(position)) end
	if not Matrix4x4 or not Matrix4x4.is_valid(value) then return end
	if not vector(Matrix4x4.x(value)) or not vector(Matrix4x4.y(value))
		or not vector(Matrix4x4.z(value)) or not vector(Matrix4x4.translation(value)) then return end
	return value
end

local function skeleton(entry)
	for _, bone in ipairs(entry.bones) do
		if not Unit.has_node(entry.outfit, bone.name) or not Unit.has_node(entry.helper, bone.name)
			or Unit.node(entry.outfit, bone.name) ~= bone.node or Unit.node(entry.helper, bone.name) ~= bone.node
			or Unit.scene_graph_parent(entry.outfit, bone.node) ~= bone.parent
			or Unit.scene_graph_parent(entry.helper, bone.node) ~= bone.parent then return false end
	end
	return true
end

local function capture(unit, entry)
	local pose = {}
	for i, bone in ipairs(entry.bones) do
		local position = vector(Unit.local_position(unit, bone.node))
		local rotation = quaternion(Unit.local_rotation(unit, bone.node))
		local scale = vector(Unit.local_scale(unit, bone.node), true)
		if not position or not rotation or not scale then return end
		pose[i] = { position = position, rotation = rotation, scale = scale }
	end
	return pose
end

local function rotation_mix(a, b, amount)
	local dot = a[1]*b[1] + a[2]*b[2] + a[3]*b[3] + a[4]*b[4]
	local sign = dot < 0 and -1 or 1
	dot = math.min(1, math.abs(dot))
	local x, y = 1-amount, amount
	if dot < 0.9995 then
		local angle = math.acos(dot)
		local sine = math.sin(angle)
		x, y = math.sin((1-amount)*angle)/sine, math.sin(amount*angle)/sine
	end
	local result, length = {}, 0
	for i = 1, 4 do result[i] = a[i]*x + b[i]*y*sign; length = length + result[i]*result[i] end
	length = math.sqrt(length)
	for i = 1, 4 do result[i] = result[i]/length end
	return result
end

local function mix(source, target, amount)
	local pose = {}
	for i = 1, BONE_COUNT do
		local a, b = source[i], target[i]
		local position, scale = {}, {}
		for axis = 1, 3 do
			position[axis] = a.position[axis]*(1-amount) + b.position[axis]*amount
			scale[axis] = a.scale[axis]*(1-amount) + b.scale[axis]*amount
		end
		pose[i] = { position = position, rotation = rotation_mix(a.rotation, b.rotation, amount), scale = scale }
	end
	return pose
end

local function write_pose(unit, entry, pose)
	for i, bone in ipairs(entry.bones) do
		local value = pose[i]
		Unit.set_local_position(unit, bone.node, Vector3(unpack(value.position)))
		Unit.set_local_rotation(unit, bone.node, Quaternion.from_elements(unpack(value.rotation)))
		Unit.set_local_scale(unit, bone.node, Vector3(unpack(value.scale)))
	end
end

local function valid_profile(profile)
	if type(profile) ~= "table" or profile.unit ~= OUTFIT
		or profile.cross_owner_transition_policy ~= "snapshot-blend-v1"
		or profile.sampler_state_machine ~= OUTFIT .. "/presentation_sampler"
		or type(profile.manifest_id) ~= "string" or #profile.manifest_id ~= 64
		or not profile.manifest_id:match("^[0-9a-f]+$")
		or type(profile.bone_names) ~= "table" or #profile.bone_names ~= BONE_COUNT
		or type(profile.states) ~= "table" or type(profile.states[profile.default_state]) ~= "table" then return false end
	for _, state in pairs(profile.states) do
		if type(state) ~= "table" or (state.owner ~= "authored" and state.owner ~= "legacy")
			or type(state.loop_animation) ~= "boolean" or type(state.visible_aim) ~= "boolean"
			or (state.speed_expression ~= "1" and state.speed_expression ~= SPEED .. " / 1.9"
				and state.speed_expression ~= SPEED .. " / 4") then return false end
	end
	return true
end

local function start(owner, outfit, profile)
	if owner and entries[owner] then remove(owner, entries[owner]) end
	local health = HEALTH_ALIVE and HEALTH_ALIVE[owner]
	if not owner or not outfit or not Unit.alive(owner) or not Unit.alive(outfit)
		or (health ~= nil and health ~= true) or not valid_profile(profile)
		or not mod._warlock_outfits or mod._warlock_outfits[owner] ~= outfit
		or Unit.get_data(outfit, "unit_name") ~= OUTFIT
		or Unit.get_data(outfit, "warlock_animation_manifest_id") ~= profile.manifest_id then return false end
	local world = Unit.world(owner)
	if not world or Unit.world(outfit) ~= world then return false end
	local entry = { world = world, outfit = outfit, profile = profile, state = profile.default_state,
		bones = {}, bone_set = {}, awaiting_health = health ~= true, frame = 0, applied_frame = -1,
		elapsed = 0, duration = 0, active = false, status = "starting" }
	-- The outer unit root follows the same carrier. root_point remains an
	-- animated skeletal node and is included in the 138-pose compositor.
	entries[owner] = entry
	local ok, result = pcall(function()
		-- Binding an unloaded resource can assert inside the native engine; a
		-- Lua pcall cannot contain that failure. Check before spawning a helper.
		if not Application or type(Application.can_get) ~= "function"
			or not Application.can_get("state_machine", profile.sampler_state_machine) then
			entry.reported = startup_reports
			diagnostic(entry, "unavailable_sampler_resource")
			return false
		end
		entry.position = vector(Unit.world_position(owner, 0))
		if not entry.position then return false end
		entry.helper = World.spawn_unit(world, OUTFIT)
		if not live(entry.helper, world) then return false end
		local count = Unit.num_meshes(entry.helper)
		if not finite(count) or count < 0 or count > 256 or count ~= math.floor(count) then return false end
		for index = 0, count-1 do
			Unit.set_mesh_visibility(entry.helper, index, false, "default")
			Unit.set_mesh_visibility(entry.helper, index, false, "shadow_caster")
		end
		Unit.set_animation_state_machine(entry.helper, profile.sampler_state_machine)
		Unit.enable_animation_state_machine(entry.helper)
		Unit.set_animation_bone_mode(entry.helper, "transform")
		Unit.set_animation_root_mode(entry.helper, "ignore")
		Unit.set_bones_lod(entry.helper, 0)
		World.link_unit(world, entry.helper, 0, owner, 0)
		local used = {}
		for i, name in ipairs(profile.bone_names) do
			if type(name) ~= "string" or used[name] or not Unit.has_node(outfit, name)
				or not Unit.has_node(entry.helper, name) then return false end
			local node = Unit.node(outfit, name)
			if node == 0 or entry.bone_set[node] or Unit.node(entry.helper, name) ~= node then return false end
			local parent = Unit.scene_graph_parent(outfit, node)
			if not finite(parent) or parent < 0 or parent >= node
				or Unit.scene_graph_parent(entry.helper, node) ~= parent then return false end
			entry.bones[i], entry.bone_set[node], used[name] = { name = name, node = node, parent = parent }, true, true
		end
		if not Unit.animation_has_variable(entry.helper, SPEED) then return false end
		entry.speed_index = Unit.animation_find_variable(entry.helper, SPEED)
		if Unit.animation_has_constraint_target(owner, AIM) and Unit.animation_has_constraint_target(entry.helper, AIM) then
			entry.aim_source = Unit.animation_find_constraint_target(owner, AIM)
			entry.aim_target = Unit.animation_find_constraint_target(entry.helper, AIM)
		end
		entry.status = "ready"
		return true
	end)
	if not ok or not result then remove(owner, entry); return false end
	return true
end

local function protected(owner, callback, ...)
	local ok, result = pcall(callback, owner, ...)
	if ok then return result end
	local entry = entries[owner]
	if entry then fail(entry, "sampler_api_error") end
	return false
end

function mod._start_warlock_animation_blend(owner, outfit, profile)
	local ok, result = pcall(start, owner, outfit, profile)
	if ok then return result end
	local entry = entries[owner]
	if entry then remove(owner, entry) end
	return false
end

local function helper_valid(owner, helper, profile)
	local entry = entries[owner]
	return entry and entry.helper == helper and (profile == nil or entry.profile == profile)
		and usable(owner, entry) and not entry.blocked and entry.active
		and entry.profile.states[entry.state].owner == "legacy" and skeleton(entry) or false
end

function mod._warlock_transition_helper_valid(owner, helper, profile)
	return protected(owner, helper_valid, helper, profile)
end

local function note_event(owner, event, from, to, blend_time)
	local entry = entries[owner]
	if not entry then return false end
	if not binding(owner, entry) then remove(owner, entry); return false end
	local ready = healthy(owner, entry)
	if entries[owner] ~= entry or entry.blocked then return false end
	if not live(entry.helper, entry.world) then return fail(entry, "missing_sampler") end
	local profile = entry.profile
	local source, target = profile.states[from], profile.states[to]
	local edge = source and source.transitions and source.transitions[event]
	if from ~= entry.state or not target or not edge or edge.to ~= to or edge.blend_time ~= blend_time
		or not finite(blend_time) or blend_time < 0 or blend_time > 1 then return fail(entry, "invalid_transition") end
	if not Unit.has_animation_event(entry.helper, event) then return fail(entry, "missing_sampler_event") end
	local bridge = entry.active or source.owner ~= target.owner
	if bridge and ready and entry.presented then
		if not skeleton(entry) then return fail(entry, "changed_skeleton") end
		local pose = entry.active and entry.displayed or capture(entry.outfit, entry)
		if entry.active and not pose then pose = entry.source end
		if not pose then return fail(entry, "invalid_displayed_pose") end
		entry.source, entry.elapsed, entry.duration = pose, 0, blend_time
		entry.active = blend_time > 0
	else
		-- Before the first evaluated frame there is no displayed outgoing pose.
		-- Preserve setup events without interpolating from a stale spawn rest.
		entry.active, entry.source = false, nil
	end
	entry.state, entry.clock_reset, entry.clock = to, true, nil
	entry.event, entry.event_frame = event, entry.frame
	entry.applied_frame = -1
	Unit.animation_event(entry.helper, event)
	entry.status = entry.active and "blending" or "native"
	return true
end

function mod._note_warlock_animation_blend_event(owner, event, from, to, blend_time)
	return protected(owner, note_event, event, from, to, blend_time)
end

local function rate(state, speed)
	if state.speed_expression == SPEED .. " / 1.9" then return speed/1.9 end
	if state.speed_expression == SPEED .. " / 4" then return speed/4 end
	return 1
end

local function update(owner, entry, world, dt)
	if not binding(owner, entry) then remove(owner, entry); return end
	if not healthy(owner, entry) or entry.world ~= world or entry.blocked then return end
	if not live(entry.helper, world) then return fail(entry, "missing_sampler") end
	entry.frame = entry.frame + 1
	if not finite(dt) or dt < 0 then return fail(entry, "invalid_animation_dt") end
	local position = vector(Unit.world_position(owner, 0))
	if not position then return fail(entry, "invalid_owner_position") end
	local root_position = vector(Unit.local_position(entry.outfit, 0))
	local root_rotation = quaternion(Unit.local_rotation(entry.outfit, 0))
	local root_scale = vector(Unit.local_scale(entry.outfit, 0), true)
	if not root_position or not root_rotation or not root_scale then return fail(entry, "invalid_sampler_root") end
	local state, target = entry.profile.states[entry.state]
	if state.visible_aim then
		if entry.aim_source == nil or entry.aim_target == nil then return fail(entry, "missing_sampler_aim") end
		target = aim(Unit.animation_get_constraint_target(owner, entry.aim_source))
		if not target then return fail(entry, "invalid_sampler_aim") end
	end
	-- Like visible locomotion, a pause or hitch invalidates the derivative.
	-- A finite hitch still evaluates animation and can complete a transition;
	-- restart its clock check from the actual post-engine target playhead.
	local discontinuity, speed = dt > 0.25, 0
	if dt > 0 and not discontinuity and entry.position then
		local dx, dy = position[1]-entry.position[1], position[2]-entry.position[2]
		local measured = math.sqrt(dx*dx + dy*dy)/dt
		if finite(measured) and measured <= 12 then speed = measured end
	end
	entry.position = dt > 0 and not discontinuity and position or nil
	if discontinuity then entry.clock, entry.clock_reset = nil, false end
	Unit.animation_set_variable(entry.helper, entry.speed_index, speed)
	Unit.set_local_position(entry.helper, 0, Vector3(unpack(root_position)))
	Unit.set_local_rotation(entry.helper, 0, Quaternion.from_elements(unpack(root_rotation)))
	Unit.set_local_scale(entry.helper, 0, Vector3(unpack(root_scale)))
	if target then Unit.animation_set_constraint_target(entry.helper, entry.aim_target, target) end
	entry.sample_dt, entry.sample_rate = dt, rate(state, speed)
	if entry.active then entry.elapsed = math.min(entry.duration, entry.elapsed + dt) end
end

function mod._update_warlock_animation_blend(world, dt)
	for owner, entry in pairs(entries) do
		local ok = pcall(update, owner, entry, world, dt)
		if not ok and entries[owner] == entry then fail(entry, "sampler_api_error") end
	end
end

local function clock_ready(entry)
	-- This is a target-clip clock, not an engine blend-weight API. Guard against
	-- a hidden helper that stopped evaluating, rather than displaying stale poses.
	local time, length = Unit.animation_layer_info(entry.helper, 1)
	entry.observed_time, entry.observed_length = time, length
	if not finite(time) or not finite(length) or time < 0 or length <= 0 or time > length + 0.002 then
		return fail(entry, "invalid_sampler_clock")
	end
	local previous = entry.clock_reset and 0 or entry.clock
	entry.previous_clock = previous
	if previous ~= nil and entry.sample_dt ~= nil then
		local step = entry.sample_dt*entry.sample_rate
		local expected = previous + step
		if entry.profile.states[entry.state].loop_animation then expected = expected % length
		else expected = math.min(length, expected) end
		entry.expected_clock = expected
		local difference = math.abs(time-expected)
		if entry.profile.states[entry.state].loop_animation then difference = math.min(difference, math.abs(length-difference)) end
		-- An event delivered after this frame's pre-animation update has zero
		-- compositor elapsed time. It may be awaiting evaluation (time zero),
		-- or already have consumed this frame's step; neither advances the blend.
		local same_frame_event = entry.clock_reset and entry.event_frame == entry.frame
		if same_frame_event and time <= math.min(length, step) + 0.002 then difference = 0 end
		if difference > math.max(0.002, step*0.05) then
			return fail(entry, "stale_sampler_clock")
		end
	end
	entry.clock, entry.clock_reset = time, false
	return true
end

local function release_ready(entry)
	-- Both independently resolved rigs must reach the same destination phase
	-- before the native visible pose resumes ownership. This does not claim to
	-- measure native blend weights or prove hidden-mesh evaluation in-game.
	local time, length = Unit.animation_layer_info(entry.outfit, 1)
	entry.observed_visible_time, entry.observed_visible_length = time, length
	if not finite(time) or not finite(length) or time < 0 or length <= 0 or time > length + 0.002 then
		return fail(entry, "invalid_visible_clock")
	end
	local difference = math.abs(time-entry.clock)
	if entry.profile.states[entry.state].loop_animation then difference = math.min(difference, math.abs(length-difference)) end
	if math.abs(length-entry.observed_length) > 0.002
		or difference > math.max(0.002, entry.sample_dt*entry.sample_rate*0.05) then
		return fail(entry, "mismatched_target_clock")
	end
	return true
end

local function legacy_target(owner, entry)
	local grip, reason = mod._prepare_warlock_legacy_grip_pose(owner, entry.helper)
	if type(grip) ~= "table" or #grip ~= 12 then return fail(entry, reason or "invalid_legacy_grip") end
	local outfit, why = mod._prepare_warlock_legacy_outfit_pose(owner, entry.helper, entry.profile, grip)
	if type(outfit) ~= "table" or #outfit ~= 7 then return fail(entry, why or "invalid_legacy_outfit") end
	local prepared, used = {}, {}
	for _, group in ipairs({grip, outfit}) do
		for _, record in ipairs(group) do
			if type(record) ~= "table" or not entry.bone_set[record.node] or used[record.node] then
				return fail(entry, "invalid_legacy_nodes")
			end
			local position, rotation = vector(record.position), quaternion(record.rotation)
			if not position or not rotation then return fail(entry, "invalid_legacy_pose") end
			prepared[#prepared+1], used[record.node] = { node = record.node, position = position, rotation = rotation }, true
		end
	end
	-- Both candidate groups are checked before the first helper setter.
	for _, record in ipairs(prepared) do
		Unit.set_local_position(entry.helper, record.node, Vector3(unpack(record.position)))
		Unit.set_local_rotation(entry.helper, record.node, Quaternion.from_elements(unpack(record.rotation)))
	end
	World.update_unit(entry.world, entry.helper)
	return true
end

local function apply(owner, outfit)
	local entry = entries[owner]
	if not usable(owner, entry) or (outfit and entry.outfit ~= outfit) or entry.blocked then return false end
	if entry.applied_frame == entry.frame then return entry.active end
	entry.applied_frame = entry.frame
	if not skeleton(entry) then return fail(entry, "changed_skeleton") end
	if not clock_ready(entry) then return false end
	entry.presented = true
	if not entry.active then return false end
	if entry.elapsed >= entry.duration then
		if not release_ready(entry) then return false end
		entry.active, entry.source, entry.displayed, entry.status = false, nil, nil, "native"
		return false
	end
	World.update_unit(entry.world, owner)
	World.update_unit(entry.world, entry.helper)
	if entry.profile.states[entry.state].owner == "legacy" and not legacy_target(owner, entry) then return false end
	local target = capture(entry.helper, entry)
	if not target then return fail(entry, "invalid_sampler_pose") end
	local pose = mix(entry.source, target, entry.elapsed/entry.duration)
	write_pose(entry.outfit, entry, pose)
	World.update_unit(entry.world, entry.outfit)
	entry.displayed, entry.status = pose, "blending"
	return true
end

function mod._apply_warlock_animation_blend(owner, outfit)
	return protected(owner, apply, outfit)
end

local function active(owner)
	local entry = entries[owner]
	if not entry then return false end
	if not binding(owner, entry) then remove(owner, entry); return false end
	if not healthy(owner, entry) then return false end
	if not live(entry.helper, entry.world) then fail(entry, "missing_sampler") end
	return entry.active or entry.blocked or false
end

function mod._warlock_animation_blend_active(owner)
	local ok, result = pcall(active, owner)
	if ok then return result end
	local entry = entries[owner]
	if entry then fail(entry, "sampler_api_error"); return true end
	return false
end

function mod._warlock_animation_blend_status(owner)
	return entries[owner] and entries[owner].status or "off"
end

function mod._stop_warlock_animation_blend(owner)
	if owner and entries[owner] then remove(owner, entries[owner]) end
end

function mod._reset_warlock_animation_blend()
	for owner, entry in pairs(entries) do remove(owner, entry) end
end

function mod._release_warlock_animation_blend_world(world)
	for owner, entry in pairs(entries) do if entry.world == world then remove(owner, entry) end end
end
