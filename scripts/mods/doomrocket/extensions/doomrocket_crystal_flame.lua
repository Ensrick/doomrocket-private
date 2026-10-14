local mod = get_mod("doomrocket")

-- #15 TEST candidate: reuse the native small, local-space pickup torch unchanged.
-- Its effect/material/parent/texture chain is verified in the pickups package.
-- Native initializer values are smaller than the rejected ground-fire effect;
-- colour and rendered appearance still require a written in-game verdict.
local EFFECT = "fx/wpnfx_torch_local_space_3p"
local PACKAGE = "resource_packages/pickups"
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
}
state.packages = state.packages or {}
state.creating_worlds = state.creating_worlds or {}
state.pending_owners = state.pending_owners or {}
state.pending_weapons = state.pending_weapons or {}
-- Older controllers could retain their breed-package reference while an
-- unknown world awaited release. Preserve that ownership across this reload;
-- never mistake it for ownership of the new pickup package or the game's refs.
if state.owns_package and state.package_manager then
	state.packages["resource_packages/breeds/skaven_warpfire_thrower"] = state.package_manager
end
state.owns_package, state.package_manager, state.size = nil, nil, nil
state.reported = {}
mod._doomrocket_crystal_flame_state = state

local function report_skip(reason)
	if not state.reported[reason] then
		state.reported[reason] = true
		printf("[doomrocket:CRYSTAL] phase=skip reason=%s effect=%s", reason, EFFECT)
	end
end

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

local function forget_pending(entry)
	if state.pending_owners[entry.owner] == entry then
		state.pending_owners[entry.owner] = nil
	end
	if state.pending_weapons[entry.weapon] == entry then
		state.pending_weapons[entry.weapon] = nil
	end
end

local function release_package_if_safe()
	for world in pairs(state.releasing_worlds) do
		if not known_world(world) then
			state.releasing_worlds[world] = nil
		end
	end

	if next(state.entries) or next(state.releasing_worlds) or next(state.unknown_worlds)
		or next(state.creating_worlds) or next(state.pending_owners) then
		return
	end

	-- Only drop references held by this module, including any old controller's
	-- retained reference. The game's global pickup reference is never touched.
	for name, manager in pairs(state.packages) do
		if manager == Managers.package and manager:has_loaded(name, PACKAGE_REFERENCE) then
			manager:unload(name, PACKAGE_REFERENCE)
		end
		state.packages[name] = nil
	end
end

local function stop(owner, reason)
	local pending = state.pending_owners[owner]
	local cancelled = pending and not pending.cancelled
	if pending then pending.cancelled = true end
	-- Claim before native calls: repeated or reentrant cleanup cannot reuse the ID.
	local entry = forget(owner)

	if not entry then
		return cancelled or false
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
		if type(value) ~= "number" or value ~= value or math.abs(value) > 1000000 then
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
	local x, y, z = anchor.x_axis, anchor.y_axis, anchor.z_axis
	local determinant = x[1] * (y[2] * z[3] - y[3] * z[2])
		- y[1] * (x[2] * z[3] - x[3] * z[2])
		+ z[1] * (x[2] * y[3] - x[3] * y[2])
	if determinant <= 1e-18 then return nil end

	-- Cyclic (y, z, x) keeps the frame right-handed and puts the crystal's
	-- mount-to-tip axis on the effect's rising +Z.
	local pose = Matrix4x4.identity()
	Matrix4x4.set_x(pose, Vector3(unpack(anchor.y_axis)))
	Matrix4x4.set_y(pose, Vector3(unpack(anchor.z_axis)))
	Matrix4x4.set_z(pose, Vector3(unpack(anchor.x_axis)))
	Matrix4x4.set_translation(pose, Vector3(unpack(anchor.position)))
	-- Keep only the measured inverse-node compensation: its 0.01 axes cancel
	-- the launcher's scale-100 mesh wrapper. The native small effect's own
	-- initializers are unchanged; no rejected radius/height scaling is applied.
	return pose
end

local function ensure_resource()
	local manager = Managers.package

	if not manager or not Application.can_get("package", PACKAGE) then
		report_skip("package_unavailable")
		return false
	end

	state.packages[PACKAGE] = manager
	if not manager:has_loaded(PACKAGE, PACKAGE_REFERENCE) then
		-- Omitted async argument means load + flush in native PackageManager.
		manager:load(PACKAGE, PACKAGE_REFERENCE)
	end

	if not manager:has_loaded(PACKAGE, PACKAGE_REFERENCE) then
		report_skip("package_not_loaded")
		return false
	elseif not Application.can_get("particles", EFFECT) then
		report_skip("effect_unavailable")
		return false
	end
	return true
end

local function create_emitter(entry, pose)
	pose = pose or anchor_pose(mod._doomrocket_crystal_anchor)
	if not pose then return nil end
	state.creating_worlds[entry.world] = (state.creating_worlds[entry.world] or 0) + 1
	local function finish_creation()
		local remaining = state.creating_worlds[entry.world] - 1
		state.creating_worlds[entry.world] = remaining > 0 and remaining or nil
		forget_pending(entry)
	end
	local function context_owned()
		return not state.releasing_worlds[entry.world] and not state.unknown_worlds[entry.world]
			and known_world(entry.world) and Unit.alive(entry.weapon)
			and Unit.world(entry.weapon) == entry.world
	end
	local function defer_cleanup()
		if not state.releasing_worlds[entry.world] then
			state.unknown_worlds[entry.world] = true
		end
		report_skip("creation_cleanup_deferred")
	end
	local function retire_created(id)
		-- Cancellation does not remove ownership; world/unit teardown can.
		local checked, playing
		if context_owned() then
			checked, playing = pcall(World.are_particles_playing, entry.world, id)
		end
		if checked and not playing then return true end
		if checked and playing and context_owned() then
			return pcall(World.destroy_particles, entry.world, id)
		end
		return false
	end
	local created, id = pcall(World.create_particles, entry.world, EFFECT, Vector3(0, 0, 0))
	if not created or type(id) ~= "number" or id ~= id or id < 0 or id == math.huge or id % 1 ~= 0 then
		finish_creation()
		-- A wrapper can allocate then error/return an invalid handle. Without a
		-- usable owned ID, only world teardown can prove the emitter is gone.
		defer_cleanup()
		report_skip("creation_failed")
		return nil
	end
	if not context_owned() then
		finish_creation()
		defer_cleanup()
		return nil
	end
	if entry.cancelled then
		local cleaned = retire_created(id)
		finish_creation()
		if not cleaned then defer_cleanup() end
		report_skip("creation_cancelled")
		return nil
	end
	local linked = pcall(World.link_particles, entry.world, id, entry.weapon, entry.node, pose, "destroy")
	if not linked then
		-- A failing wrapper could already have linked then deleted the launcher
		-- or released the world. Its integer ID could then name another emitter.
		local cleaned = retire_created(id)
		finish_creation()
		if not cleaned then
			-- The engine owns any uncertain emitter until this world is released.
			-- Keep the package reference and prohibit further spawns in that world.
			defer_cleanup()
		end
		report_skip("link_failed")
		return nil
	end
	if not context_owned() then
		finish_creation()
		defer_cleanup()
		return nil
	end
	if entry.cancelled then
		local cleaned = retire_created(id)
		finish_creation()
		if not cleaned then defer_cleanup() end
		report_skip("creation_cancelled")
		return nil
	end
	finish_creation()
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

	if not weapon or state.weapons[weapon] or state.pending_owners[owner] or state.pending_weapons[weapon] then
		return false
	end

	local pose = anchor_pose(anchor)

	if not pose or not Unit.has_node(weapon, anchor.node) then
		return false
	end
	local node = Unit.node(weapon, anchor.node)
	local entry = { owner = owner, weapon = weapon, world = world, node = node }
	state.pending_owners[owner], state.pending_weapons[weapon] = entry, entry
	local checked, resident = pcall(ensure_resource)
	if not checked or not resident then
		if not checked then report_skip("resource_error") end
		forget_pending(entry)
		release_package_if_safe()
		return false
	end
	if entry.cancelled then
		forget_pending(entry)
		release_package_if_safe()
		report_skip("creation_cancelled")
		return false
	end
	local id = create_emitter(entry, pose)

	if type(id) ~= "number" then
		release_package_if_safe()
		return false
	end

	entry.id = id

	state.entries[owner] = entry
	state.weapons[weapon] = owner
	printf("[doomrocket:CRYSTAL] phase=start effect=%s node=%s profile=native_small_pickup_torch scale=anchor_compensation_only colour=unverified rendered_size=unverified",
		EFFECT, anchor.node)
	return true
end

mod._stop_warlock_crystal_flame = function (owner, reason)
	return stop(owner, reason or "unspecified")
end

mod._stop_warlock_crystal_flame_item = function (owner, item, reason)
	local entry = state.entries[owner] or state.pending_owners[owner]

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
	for _, pending in pairs(state.pending_owners) do pending.cancelled = true end

	for owner in pairs(state.entries) do
		owners[#owners + 1] = owner
	end

	for i = 1, #owners do
		stop(owners[i], reason or "reset")
	end

	release_package_if_safe()
end

-- Compatibility for an old hot-reloaded caller: numeric tuning is retired.
-- The small native effect is used unchanged, so this cannot recreate, resize,
-- enable or otherwise mutate any emitter.
mod._set_warlock_crystal_flame_size = function ()
	return false, "native_effect"
end

mod:command("warlock_crystal_flame", "Describe the native small crystal-flame TEST candidate; size tuning is retired", function ()
	mod:echo("Crystal flame TEST candidate: unchanged native pickup torch. Numeric size tuning is retired; colour and rendered appearance await in-game testing.")
end)

mod._release_warlock_crystal_flame_world = function (world)
	-- Called BEFORE Application.release_world: the engine frees every particle,
	-- so neither particle calls nor a package unload are safe or needed here.
	local owners = {}
	local pending_in_world = false
	for _, pending in pairs(state.pending_owners) do
		if pending.world == world then
			pending.cancelled = true
			pending_in_world = true
		end
	end

	for owner, entry in pairs(state.entries) do
		if entry.world == world then
			owners[#owners + 1] = owner
		end
	end

	for i = 1, #owners do
		forget(owners[i])
	end

	if #owners > 0 or state.unknown_worlds[world] or state.creating_worlds[world] or pending_in_world then
		state.releasing_worlds[world] = true
	end

	state.unknown_worlds[world] = nil
end

return
