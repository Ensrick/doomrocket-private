local mod = get_mod("doomrocket")

-- #15: a persistent warpfire flame on the crystal under the launcher barrel.
-- Lifecycle follows the accepted backpack smoke: one linked effect per live
-- carried launcher on each peer, never re-created per frame, stopped before
-- death, drop or inventory teardown, and forgotten before world release.
-- v0.1.83 linked the Warpfire nozzle effect; it was created on every Engineer
-- but Crunch saw no flame. This uses the Warpfire Thrower's persistent green
-- ground fire instead, sized through its own vanilla size variable
-- (DamageBlobExtension starts it at radius 0.6, height 1.2 and grows it). Its
-- flames rise along local +Z, so +Z is laid along the crystal, mount to tip.
local EFFECT = "fx/chr_warp_fire_flamethrower_remains_01"
local SIZE_VARIABLE = "warp_fire_flamethrower_remains_size"
local DEFAULT_SIZE = { 0.06, 0.2 }
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
			-- A deleted launcher already destroyed its linked emitter. Do NOT query the
			-- old ID: another effect may now own that integer in the same world.
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

local function apply_size(entry)
	local variable = World.find_particles_variable(entry.world, EFFECT, SIZE_VARIABLE)

	World.set_particles_variable(entry.world, entry.id, variable, Vector3(state.size[1], state.size[2], 0))
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
	if DEDICATED_SERVER or not owner or not Unit.alive(owner) then
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
	local id = ScriptWorld.create_particles_linked(world, EFFECT, weapon, node, "destroy", pose)

	if type(id) ~= "number" then
		return false
	end

	local entry = { weapon = weapon, world = world, id = id }

	state.entries[owner] = entry
	state.weapons[weapon] = owner
	apply_size(entry)
	printf("[doomrocket:CRYSTAL] phase=start effect=%s node=%s radius=%.3f height=%.3f",
		EFFECT, anchor.node, state.size[1], state.size[2])
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

-- TEST tuning: resize every live flame on this peer and all later ones.
mod._set_warlock_crystal_flame_size = function (radius, height)
	radius, height = tonumber(radius), tonumber(height)

	if not radius or not height or radius ~= radius or height ~= height then
		return false
	end

	state.size[1] = math.min(math.max(radius, MIN_SIZE), MAX_SIZE)
	state.size[2] = math.min(math.max(height, MIN_SIZE), MAX_SIZE)

	for _, entry in pairs(state.entries) do
		if not state.releasing_worlds[entry.world] and known_world(entry.world) and Unit.alive(entry.weapon) then
			apply_size(entry)
		end
	end

	printf("[doomrocket:CRYSTAL] phase=resize radius=%.3f height=%.3f", state.size[1], state.size[2])
	return true
end

mod:command("warlock_crystal_flame", "TEST: crystal flame size in metres: /warlock_crystal_flame <radius> <height>", function (radius, height)
	if mod._set_warlock_crystal_flame_size(radius, height) then
		mod:echo(string.format("Crystal flame size: radius %.3f m, height %.3f m", state.size[1], state.size[2]))
	else
		mod:echo("Usage: /warlock_crystal_flame <radius> <height>   (current: %.3f %.3f)", state.size[1], state.size[2])
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
