local mod = get_mod("doomrocket")

-- #15: temporarily omit the gem particle after Crunch's repeated size failure.
-- Neither the damage-blob variable nor the scaled Vortex attachment pattern has
-- produced an accepted small flame for this ground-fire effect. Keep its measured
-- anchor and dormant lifecycle for a future reviewed replacement; no runtime
-- command can enable this rejected visual on the stable candidate.
local ENABLED = false
local EFFECT = "fx/chr_warp_fire_flamethrower_remains_01"
local DEFAULT_SIZE = { 0.06, 0.2 }
-- Reference dimensions of the dormant attachment-scale experiment. These do
-- not establish rendered billboard dimensions or a working whole-effect scale.
local REFERENCE_RADIUS, REFERENCE_HEIGHT = 0.6, 1.2
-- These are bounds of our old experiment command, not measured engine limits.
-- In particular, the reported 0.010 minimum came from this clamp. A successful
-- link/resize call does not establish the billboard's rendered dimensions.
local MIN_SIZE, MAX_SIZE = 0.01, 2
local PACKAGE = "resource_packages/breeds/skaven_warpfire_thrower"
local PACKAGE_REFERENCE = "doomrocket_crystal_flame"
local WEAPON = "units/rocket/pRocketLauncher"

-- Dispose through the OLD owner before replacing its functions on a Lua reload.
if mod._reset_warlock_crystal_flame then
	mod._reset_warlock_crystal_flame("module_reload")
end

local state = mod._doomrocket_crystal_flame_state or {
	entries = {},
	weapons = {},
	releasing_worlds = {},
	unknown_worlds = {},
	size = { DEFAULT_SIZE[1], DEFAULT_SIZE[2] },
}
mod._doomrocket_crystal_flame_state = state

local function active_world()
	local manager = Managers.world

	if manager and manager:has_world("level_world") then
		return manager:world("level_world")
	end
end

local function known_world(world)
	local manager = Managers.world

	-- Paused/disabled worlds still own their particles: neither forget nor duplicate.
	return world and manager and (active_world() == world
		or manager._disabled_worlds and manager._disabled_worlds.level_world == world)
end

local function forget(owner)
	local entry = state.entries[owner]
	state.entries[owner] = nil

	if entry and state.weapons[entry.weapon] == owner then
		state.weapons[entry.weapon] = nil
	end

	return entry
end

local function release_package_if_safe()
	for world in pairs(state.releasing_worlds) do
		if not known_world(world) then
			state.releasing_worlds[world] = nil
		end
	end

	if next(state.entries) or next(state.releasing_worlds) or next(state.unknown_worlds) then
		return
	end

	local manager = state.package_manager

	-- Only ever drop this module's own reference to the shared breed package.
	if state.owns_package and manager == Managers.package and manager:has_loaded(PACKAGE, PACKAGE_REFERENCE) then
		manager:unload(PACKAGE, PACKAGE_REFERENCE)
	end

	state.owns_package = nil
	state.package_manager = nil
end

local function stop(owner, reason)
	-- Claim before native calls: repeated or reentrant cleanup cannot reuse the ID.
	local entry = forget(owner)

	if not entry then
		return false
	end

	if not state.releasing_worlds[entry.world] then
		if known_world(entry.world) then
			if Unit.alive(entry.weapon) then
				if Unit.world(entry.weapon) == entry.world then
					if World.are_particles_playing(entry.world, entry.id) then
						World.destroy_particles(entry.world, entry.id)
					end
				else
					state.unknown_worlds[entry.world] = true
				end
			end
			-- Deleting a linked launcher destroys its emitter. Its old ID may have
			-- been recycled, so never query or destroy it after unit deletion.
		else
			state.unknown_worlds[entry.world] = true
		end
	end

	printf("[doomrocket:CRYSTAL] phase=stop reason=%s", tostring(reason))
	return true
end

local function valid_vector(values)
	if type(values) ~= "table" or #values ~= 3 then
		return false
	end

	for i = 1, 3 do
		local value = values[i]
		if type(value) ~= "number" or value ~= value or math.abs(value) == math.huge then
			return false
		end
	end

	return true
end

local function anchor_pose(anchor)
	if type(anchor) ~= "table" or anchor.node ~= "pRocketLauncher"
		or not valid_vector(anchor.x_axis) or not valid_vector(anchor.y_axis)
		or not valid_vector(anchor.z_axis) or not valid_vector(anchor.position) then
		return nil
	end

	-- Cyclic (y, z, x) keeps the frame right-handed and puts the crystal's
	-- mount-to-tip axis on the effect's rising +Z.
	local pose = Matrix4x4.identity()
	Matrix4x4.set_x(pose, Vector3(unpack(anchor.y_axis)))
	Matrix4x4.set_y(pose, Vector3(unpack(anchor.z_axis)))
	Matrix4x4.set_z(pose, Vector3(unpack(anchor.x_axis)))
	Matrix4x4.set_translation(pose, Vector3(unpack(anchor.position)))
	-- Native VortexExtension scales the local attachment pose before linking.
	-- Multiply the inverse-node compensation by the requested visual scale;
	-- replacing it with an absolute scale would expand the effect 100 times.
	local radius_scale = state.size[1] / REFERENCE_RADIUS
	local height_scale = state.size[2] / REFERENCE_HEIGHT
	Matrix4x4.set_scale(pose, Vector3(
		Vector3.length(Vector3(unpack(anchor.y_axis))) * radius_scale,
		Vector3.length(Vector3(unpack(anchor.z_axis))) * radius_scale,
		Vector3.length(Vector3(unpack(anchor.x_axis))) * height_scale))
	return pose
end

local function ensure_resource()
	local manager = Managers.package

	if not manager or not Application.can_get("package", PACKAGE) then
		return false
	end

	if not manager:has_loaded(PACKAGE, PACKAGE_REFERENCE) then
		-- Omitted async argument means load + flush in native PackageManager.
		manager:load(PACKAGE, PACKAGE_REFERENCE)
	end

	state.package_manager = manager
	state.owns_package = true
	return manager:has_loaded(PACKAGE, PACKAGE_REFERENCE)
		and Application.can_get("particles", EFFECT)
end

local function create_emitter(entry, pose)
	pose = pose or anchor_pose(mod._doomrocket_crystal_anchor)
	if not pose then return nil end
	local id = World.create_particles(entry.world, EFFECT, Vector3(0, 0, 0))
	if type(id) == "number" then
		World.link_particles(entry.world, id, entry.weapon, entry.node, pose, "destroy")
	end
	return id
end

local function carried_launcher(owner, inventory, world)
	if not inventory or inventory.unit ~= owner or inventory.dropped then
		return nil
	end

	for _, unit in pairs(inventory.inventory_item_units or {}) do
		if Unit.alive(unit) and Unit.world(unit) == world and Unit.get_data(unit, "unit_name") == WEAPON then
			local item = ScriptUnit.has_extension(unit, "ai_inventory_item_system")

			if item and not item.dropped then
				return unit
			end
		end
	end
end

mod._start_warlock_crystal_flame = function (owner, inventory)
	if not ENABLED or DEDICATED_SERVER or not owner or not Unit.alive(owner) then
		return false
	end

	local world = active_world()

	if not world or state.releasing_worlds[world] or state.unknown_worlds[world] or Unit.world(owner) ~= world then
		return false
	end

	local weapon = carried_launcher(owner, inventory, world)
	local existing = state.entries[owner]

	if existing and existing.weapon == weapon then
		return true
	elseif existing then
		stop(owner, "launcher_replaced")
	end

	local anchor = mod._doomrocket_crystal_anchor

	if not weapon or state.weapons[weapon] or type(anchor) ~= "table" or not Unit.has_node(weapon, anchor.node) then
		return false
	end

	local pose = anchor_pose(anchor)

	if not pose or not ensure_resource() then
		return false
	end

	local node = Unit.node(weapon, anchor.node)
	local entry = { weapon = weapon, world = world, node = node }
	local id = create_emitter(entry, pose)

	if type(id) ~= "number" then
		return false
	end

	entry.id = id

	state.entries[owner] = entry
	state.weapons[weapon] = owner
	printf("[doomrocket:CRYSTAL] phase=start effect=%s node=%s input_radius=%.3f input_height=%.3f link_scale_xy=%.3f link_scale_z=%.3f rendered_size=unverified",
		EFFECT, anchor.node, state.size[1], state.size[2], state.size[1] / REFERENCE_RADIUS,
		state.size[2] / REFERENCE_HEIGHT)
	return true
end

mod._stop_warlock_crystal_flame = function (owner, reason)
	return stop(owner, reason or "unspecified")
end

mod._stop_warlock_crystal_flame_item = function (owner, item, reason)
	local entry = state.entries[owner]

	if entry and entry.weapon == item then
		return stop(owner, reason or "item_removed")
	end

	return false
end

mod._update_warlock_crystal_flame = function ()
	if not ENABLED then
		return
	end

	local stopped = {}

	for owner, entry in pairs(state.entries) do
		if not Unit.alive(owner) or not Unit.alive(entry.weapon) or not known_world(entry.world) then
			stopped[#stopped + 1] = owner
		end
	end

	for i = 1, #stopped do
		stop(stopped[i], "context_removed")
	end
end

mod._reset_warlock_crystal_flame = function (reason)
	local owners = {}

	for owner in pairs(state.entries) do
		owners[#owners + 1] = owner
	end

	for i = 1, #owners do
		stop(owners[i], reason or "reset")
	end

	release_package_if_safe()
end

-- Retained experiment; the shipping omission must not claim successful tuning.
mod._set_warlock_crystal_flame_size = function (radius, height)
	if not ENABLED then
		return false, "disabled"
	end

	radius, height = tonumber(radius), tonumber(height)

	if not radius or not height or radius ~= radius or height ~= height
		or math.abs(radius) == math.huge or math.abs(height) == math.huge then
		return false
	end

	state.size[1] = math.min(math.max(radius, MIN_SIZE), MAX_SIZE)
	state.size[2] = math.min(math.max(height, MIN_SIZE), MAX_SIZE)

	local restarted = 0

	for owner, entry in pairs(state.entries) do
		if not state.releasing_worlds[entry.world] and not state.unknown_worlds[entry.world]
			and known_world(entry.world) and Unit.alive(owner) and Unit.alive(entry.weapon)
			and Unit.world(owner) == entry.world and Unit.world(entry.weapon) == entry.world then
			-- Recreate at the newly scaled link pose, so particles emitted at the
			-- previous size cannot obscure the immediate comparison.
			if World.are_particles_playing(entry.world, entry.id) then
				World.destroy_particles(entry.world, entry.id)
			end
			local id = create_emitter(entry)
			if type(id) == "number" then
				entry.id = id
				restarted = restarted + 1
			else
				-- The old emitter is gone; never retain its recycled integer if
				-- the engine did not return a replacement handle.
				forget(owner)
				printf("[doomrocket:CRYSTAL] phase=stop reason=resize_creation_failed")
			end
		end
	end

	printf("[doomrocket:CRYSTAL] phase=resize input_radius=%.3f input_height=%.3f link_scale_xy=%.3f link_scale_z=%.3f live=%d rendered_size=unverified",
		state.size[1], state.size[2], state.size[1] / REFERENCE_RADIUS, state.size[2] / REFERENCE_HEIGHT, restarted)
	return true, restarted
end

mod:command("warlock_crystal_flame", "Crystal flame is temporarily disabled pending a working small effect", function (radius, height)
	local valid, restarted = mod._set_warlock_crystal_flame_size(radius, height)
	if restarted == "disabled" then
		mod:echo("Crystal flame is temporarily disabled: the previous effect did not respond visibly to size changes. The old 0.010 minimum was our command's clamp; it did not establish an engine limit.")
	elseif valid then
		mod:echo(string.format("Experimental flame inputs: radius %.3f, height %.3f (%d live emitters recreated). Rendered size is unverified; inputs are clamped by this mod to %.3f-%.3f.", state.size[1], state.size[2], restarted, MIN_SIZE, MAX_SIZE))
	else
		mod:echo("Usage: /warlock_crystal_flame <radius> <height>   (current inputs: %.3f %.3f; mod bounds: %.3f-%.3f; rendered size unverified)", state.size[1], state.size[2], MIN_SIZE, MAX_SIZE)
	end
end)

mod._release_warlock_crystal_flame_world = function (world)
	-- Called BEFORE Application.release_world: the engine frees every particle,
	-- so neither particle calls nor a package unload are safe or needed here.
	local owners = {}

	for owner, entry in pairs(state.entries) do
		if entry.world == world then
			owners[#owners + 1] = owner
		end
	end

	for i = 1, #owners do
		forget(owners[i])
	end

	if #owners > 0 or state.unknown_worlds[world] then
		state.releasing_worlds[world] = true
	end

	state.unknown_worlds[world] = nil
end

return
