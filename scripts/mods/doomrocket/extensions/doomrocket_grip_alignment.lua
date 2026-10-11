local mod = get_mod("doomrocket")

-- The launcher is linked to the native Ratling, but the visible arms used an
-- independently advancing animation machine. Match the twelve upper-body
-- deform joints to the carrier's evaluated rigid world pose. Keep the custom
-- hierarchy, scales, lower-body gait, own ASM, and native weapon links intact.
-- Never copy a native local pose into the custom rig's 100x parent space.
local OUTFIT = "units/warlock_bombardier/warlock_bombardier_3p"
local WEAPON = "units/rocket/pRocketLauncher"
local NAMES = {
	"j_spine", "j_spine1", "j_leftshoulder", "j_rightshoulder",
	"j_leftarm", "j_rightarm", "j_leftforearm", "j_rightforearm",
	"j_lefthand", "j_righthand", "j_leftforearmroll", "j_rightforearmroll",
}

if mod._reset_warlock_grip_alignment then
	mod._reset_warlock_grip_alignment()
end

local entries, pending, epoch = {}, {}, 0

local function finite(n)
	return type(n) == "number" and n == n and math.abs(n) < math.huge
end

local function live(unit, world)
	return unit and Unit.alive(unit) and Unit.world(unit) == world
end

local function valid(owner, entry)
	return live(owner, entry.world) and live(entry.outfit, entry.world)
		and HEALTH_ALIVE and HEALTH_ALIVE[owner]
		and mod._warlock_outfits and mod._warlock_outfits[owner] == entry.outfit
end

local function orthogonal(pose)
	if not Matrix4x4.is_valid(pose) then return false end
	local x, y, z = Matrix4x4.x(pose), Matrix4x4.y(pose), Matrix4x4.z(pose)
	local a, b, c = Vector3.length(x), Vector3.length(y), Vector3.length(z)
	return a > 0.000001 and b > 0.000001 and c > 0.000001
		and math.abs(Vector3.dot(x, y)) < a * b * 0.0001
		and math.abs(Vector3.dot(x, z)) < a * c * 0.0001
		and math.abs(Vector3.dot(y, z)) < b * c * 0.0001, a, b, c
end

local function times(v, scale)
	return Vector3(v.x * scale, v.y * scale, v.z * scale)
end

local function apply(owner, entry)
	-- Both units need their freshly evaluated local bones composed before reading
	-- world poses. pre_scene_update alone does not establish this cache boundary.
	World.update_unit(entry.world, owner)
	World.update_unit(entry.world, entry.outfit)
	if live(entry.weapon, entry.world) then
		World.update_unit(entry.world, entry.weapon)
	end
	if not entry.mirrored then
		-- There are no authored jump clips on the custom rig. Pulling only the
		-- upper torso onto a jumping native pelvis would stretch the body.
		entry.status = "unsupported_event"
		return
	end

	local root = Unit.world_position(owner, 0)
	local desired, locals, graph = {}, {}, {}
	for i = 1, #entry.pairs do
		local pair = entry.pairs[i]
		local target_world = Unit.world_pose(entry.outfit, pair.target)
		local ok, a, b, c = orthogonal(target_world)
		if not ok or math.abs(a - b) > a * 0.0001 or math.abs(a - c) > a * 0.0001 then
			entry.status = "unsupported_scale"
			return
		end
		local source_position = Unit.world_position(owner, pair.source)
		if not Vector3.is_valid(source_position) or Vector3.distance(source_position, root) > 4 then
			entry.status = "invalid_source"
			return
		end
		-- Reject spawn transients or an unsupported torso displacement. No offset
		-- calibration may be captured from an unevaluated initial animation pose.
		if pair.name == "j_spine" and Vector3.distance(source_position,
			Unit.world_position(entry.outfit, pair.target)) > 0.5 then
			entry.status = "unsettled_torso"
			return
		end
		local pose = Matrix4x4.from_quaternion_position(
			Unit.world_rotation(owner, pair.source), source_position)
		if not orthogonal(pose) then entry.status = "invalid_source"; return end
		-- Preserve the custom uniform world scale, not the native animated scale.
		Matrix4x4.set_x(pose, times(Matrix4x4.x(pose), a))
		Matrix4x4.set_y(pose, times(Matrix4x4.y(pose), a))
		Matrix4x4.set_z(pose, times(Matrix4x4.z(pose), a))
		desired[pair.target] = pose
	end

	local function parent_world(node)
		if desired[node] then return desired[node] end
		if graph[node] then return graph[node] end
		if node == 0 then return Unit.world_pose(entry.outfit, 0) end
		local parent = entry.parents[node]
		local pose = Matrix4x4.multiply(Unit.local_pose(entry.outfit, node), parent_world(parent))
		graph[node] = pose
		return pose
	end
	-- Resolve the entire candidate through the custom parent graph before any
	-- native write. Scale, shear, NaN and singular-parent failures leave it alone.
	for i = 1, #entry.pairs do
		local pair = entry.pairs[i]
		local parent = parent_world(pair.parent)
		if not orthogonal(parent) then entry.status = "invalid_parent"; return end
		local pose = Matrix4x4.multiply(desired[pair.target], Matrix4x4.inverse(parent))
		local ok, a, b, c = orthogonal(pose)
		local scale = Unit.local_scale(entry.outfit, pair.target)
		if not ok or not Vector3.is_valid(scale)
			or math.abs(a - scale.x) > 0.001 or math.abs(b - scale.y) > 0.001
			or math.abs(c - scale.z) > 0.001 then
			entry.status = "unsupported_local_scale"
			return
		end
		locals[i] = pose
	end
	for i = 1, #entry.pairs do
		Unit.set_local_rotation(entry.outfit, entry.pairs[i].target, Matrix4x4.rotation(locals[i]))
		Unit.set_local_position(entry.outfit, entry.pairs[i].target, Matrix4x4.translation(locals[i]))
	end
	World.update_unit(entry.world, entry.outfit)
	entry.status = "active"
end

function mod._start_warlock_grip_alignment(owner, outfit, inventory)
	if owner then entries[owner] = nil end
	if not owner or not Unit.alive(owner) or not outfit or not Unit.alive(outfit)
		or not mod._warlock_outfits or mod._warlock_outfits[owner] ~= outfit
		or Unit.get_data(outfit, "unit_name") ~= OUTFIT then return false end
	local world = Unit.world(owner)
	if not world or Unit.world(outfit) ~= world then return false end
	local node_pairs, parents = {}, {}
	for i = 1, #NAMES do
		local name = NAMES[i]
		if not Unit.has_node(owner, name) or not Unit.has_node(outfit, name) then return false end
		local target = Unit.node(outfit, name)
		local parent = Unit.scene_graph_parent(outfit, target)
		node_pairs[i] = { name = name, target = target, source = Unit.node(owner, name), parent = parent }
		local node, guard = target, 0
		while node ~= 0 and not parents[node] do
			local ancestor = Unit.scene_graph_parent(outfit, node)
			if not ancestor or ancestor == node or guard >= 256 then return false end
			parents[node] = ancestor
			node, guard = ancestor, guard + 1
		end
	end
	local weapon
	for _, item in pairs(inventory and inventory.inventory_item_units or {}) do
		if live(item, world) and Unit.get_data(item, "unit_name") == WEAPON then weapon = item; break end
	end
	entries[owner] = { world = world, outfit = outfit, weapon = weapon, pairs = node_pairs,
		parents = parents, mirrored = true, status = "armed" }
	return true
end

function mod._note_warlock_grip_alignment_event(owner, event, mirrored)
	local entry = entries[owner]
	if entry then entry.mirrored = mirrored == true end
end

function mod._warlock_grip_alignment_status(owner)
	return entries[owner] and entries[owner].status or "off"
end

function mod._stop_warlock_grip_alignment(owner)
	entries[owner] = nil
end

function mod._reset_warlock_grip_alignment()
	entries, pending, epoch = {}, {}, epoch + 1
end

function mod._release_warlock_grip_alignment_world(world)
	pending = {}
	epoch = epoch + 1
	for owner, entry in pairs(entries) do
		if entry.world == world then entries[owner] = nil end
	end
end

function mod._queue_warlock_grip_alignment(world, dt)
	if pending[world] or not next(entries) or not finite(dt) or dt <= 0 or dt > 0.25 then return end
	local entity = Managers.state.entity
	local animation = entity and entity:system("animation_system")
	if not animation then return end
	local queued_epoch = epoch
	pending[world] = true
	animation:add_safe_animation_callback(function()
		if epoch ~= queued_epoch then return end
		pending[world] = nil
		for owner, entry in pairs(entries) do
			if entry.world == world then
				if valid(owner, entry) then
					if not mod:pcall(apply, owner, entry) then entries[owner] = nil end
				else entries[owner] = nil end
			end
		end
	end)
end
