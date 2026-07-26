local mod = get_mod("doomrocket")

local new_packages = {
    "resource_packages/breeds/skaven_doomrocket",
}
local pacakge_tisch = {}

for k,v in ipairs(new_packages) do
    pacakge_tisch[v] = v
end

mod:hook(PackageManager, "load",
         function(func, self, package_name, reference_name, callback,
                  asynchronous, prioritize)
    if package_name ~= pacakge_tisch[package_name]then
        func(self, package_name, reference_name, callback, asynchronous,
             prioritize)
    end

end)

mod:hook(PackageManager, "unload",
         function(func, self, package_name, reference_name)
    if package_name ~= pacakge_tisch[package_name] then
        func(self, package_name, reference_name)
    end

end)

mod:hook(PackageManager, "has_loaded",
         function(func, self, package, reference_name)
    if package == pacakge_tisch[package] then
        return true
    end

    return func(self, package, reference_name)
end)



-- mod:hook(MatchmakingManager, "update", function(func, self, dt, ...)

--     for k,v in pairs(BLACKBOARDS) do
--         if v.breed.name == "skaven_doomrocket" then

--             for i,j in pairs(v) do
--                 if v.action then
--                     mod:echo(v.action.name)
--                 end
--             end
--         end
--     end

--     func(self, dt, ...)
-- end)

-- mod:hook(UnitSpawner,"spawn_network_unit", function (func, self, unit_name, unit_template_name, extension_init_data, position, rotation, material)
--     mod:echo(unit_template_name)
--     -- for k,v in pairs(extension_init_data) do
--     --     print(tostring(k).." = {")
--     --     for i,j in pairs(v) do
--     --         print("     "..i..   " = "..tostring(j)..",")
--     --     end
--     --     print("}")
--     -- end
--     return func(self, unit_name, unit_template_name, extension_init_data, position, rotation, material)
-- end)

-- local player = Managers.player:local_player()
-- local player_unit = player.player_unit
-- local position = Unit.local_position(player_unit, 0) + Vector3(0,0,1)
-- -- local unit_name = "units/weapons/enemy/wpn_skaven_ratlinggun/wpn_skaven_ratlinggun"
-- local unit_name = "units/weapons/enemy/wpn_skaven_set/wpn_skaven_halberd_41"
-- local unit = Managers.state.unit_spawner:spawn_local_unit(unit_name, position)

-- local data = Unit.has_node(unit, "weapon")
-- mod:echo(data)
-- mod:hook(WwiseWorld, "trigger_event", function(func, self, event_name, ...)
--     mod:echo(event_name)
--     return func(self, event_name)
-- end)


--this stuff probably needs to be in it's own mod or reworked to be more dynamic

local new_breeds = {
    "skaven_doomrocket",
}
local breeds_to_force_spawn = {}
for k,v in ipairs(new_breeds) do
    breeds_to_force_spawn[v] = v
end

-- Vanilla 6.11.3 gates the spawn queue on EnemyPackageLoader:is_breed_loaded_on_all_peers.
-- The old breed_loaded_on_all_peers table and update_breeds_loading_status() are both gone,
-- so the previous full-body replacement of ConflictDirector.update_spawn_queue nil-called
-- every spawn tick. Declaring our breeds loaded is all that replacement actually achieved.
mod:hook("EnemyPackageLoader", "is_breed_loaded_on_all_peers", function(func, self, breed_name)
	if breeds_to_force_spawn[breed_name] then
		return true
	end

	return func(self, breed_name)
end)


local breed_to_breed_stats = {}
for i,breed in ipairs(new_breeds) do
    breed_to_breed_stats[breed] = "skaven_ratling_gunner"
end
--some reason have to hook whole stats function
-- These two only ever existed to remap our custom breed onto the ratling gunner's
-- stat path (there is no statistics entry for skaven_doomrocket). Vanilla 6.11.3
-- rewrote both to go through self:_get_or_create_stat, so the old hand-rolled table
-- walk nil-derefs on any not-yet-created path and its fallback corrupted the root
-- stats node. Remap the arguments and let vanilla do the work.
local function _remap_breed_args(...)
	local n = select("#", ...)
	local args = { ... }

	for i = 1, n do
		local mapped = breed_to_breed_stats[args[i]]

		if mapped then
			args[i] = mapped
		end
	end

	return unpack(args, 1, n)
end

mod:hook(StatisticsDatabase, "modify_stat_by_amount", function (func, self, id, ...)
	return func(self, id, _remap_breed_args(...))
end)

mod:hook(StatisticsDatabase, "increment_stat", function (func, self, id, ...)
	return func(self, id, _remap_breed_args(...))
end)



local new_animations = {
	doomrocket_reload_start = {
		timing = 0.5,
		emitted_event = "anim_cb_attack_windup_start_finished"
	},
}

mod:hook(UnitSpawner, "create_unit_extensions", function(func, self, world, unit, unit_template_name, extension_init_data)

	if extension_init_data then
		if extension_init_data.locomotion_system then
			if extension_init_data.locomotion_system.breed then
				if extension_init_data.locomotion_system.breed.name == "skaven_doomrocket" then
					if Unit.alive(unit) then
						for animaiton_event, details in pairs(new_animations) do
							Unit.set_data(unit, animaiton_event, "timing", details.timing)
							Unit.set_data(unit, animaiton_event, "emitted_event", details.emitted_event)
						end

						mod.anim_emitters[unit] = AnimEmitter:new(unit, blackboard)

						Unit.set_mesh_visibility(unit, 0, false, "default")--far tank LOD
						Unit.set_mesh_visibility(unit, 4, false, "default") --far belt LOD
						Unit.set_mesh_visibility(unit, 5, false, "default") -- medium tank LOD

						Unit.set_mesh_visibility(unit, 9, false, "default") --medium belt LOD
						Unit.set_mesh_visibility(unit, 11, false, "default")--close tank LOD gunner
						Unit.set_mesh_visibility(unit, 12, false, "default")--close tank glow LOD gunner
						Unit.set_mesh_visibility(unit, 16, false, "default")--close belt LOD gunner
					end
				end
			end
		end
	end

	return func(self, world, unit, unit_template_name, extension_init_data)
end)


local alt_events = {
	-- doomrocket_reload = "units/bombadier/bombadier"
	wind_up_start = {
		machine = "units/bombadier/bombadier",
		event = "doomrocket_reload_start",
	},
	wind_up_loop = {
		machine = "units/bombadier/bombadier",
		event = "doomrocket_reload_loop",
	},
}
-- mod:hook(Unit, "animation_event", function(func, unit, event, ...)

--     if not Unit.has_animation_event(unit, event) then
-- 		local unit_name = Unit.get_data(unit, "breed")
-- 		mod:echo(unit_name)
-- 		if unit_name == "units/beings/enemies/skaven_ratlinggunner/chr_skaven_ratlinggunner" then
-- 			if alt_events[event] then
-- 				Unit.set_animation_state_machine(unit, alt_events[event])
-- 			else
-- 				Unit.set_animation_state_machine(unit, "units/beings/enemies/skaven_ratlinggunner/chr_skaven_ratlinggunner")
-- 			end
-- 		end
-- 	end



--     return func(unit, event, ...)
-- end)

local set_animation_state_machine = Unit.set_animation_state_machine
local has_animation_event = Unit.has_animation_event
local unit_get_data = Unit.get_data

-- Doomrocket owner unit -> warlock outfit unit riding it (weak: entries die
-- with the units). Registered when the outfit is swapped onto the ratling
-- state machine in the _setup_configuration hook below.
mod._warlock_outfits = mod._warlock_outfits or setmetatable({}, { __mode = "kv" })

mod:hook(Unit, "animation_event", function(func, unit, event, ...)
	-- Replay the donor rat's animation events on the warlock body so it plays
	-- the same vanilla ratling clips in lockstep (the rig was authored to fit
	-- the gun rat's animation set). Events the outfit's state machine lacks
	-- are skipped, so this stays safe if the vocabularies ever diverge.
	local outfit = mod._warlock_outfits[unit]

	if outfit then
		if Unit.alive(outfit) then
			if has_animation_event(outfit, event) then
				func(outfit, event, ...)
			end
		else
			mod._warlock_outfits[unit] = nil
		end
	end

	return func(unit, event, ...)
end)

-- Locomotion blend speeds and aim come through animation variables and
-- constraint targets, not events. The outfit runs the IDENTICAL ratling state
-- machine, so raw variable/constraint indices are layout-compatible; pcall
-- guards the mirror in case the outfit fell back to its own idle machine.
mod:hook(Unit, "animation_set_variable", function(func, unit, index, value, ...)
	local outfit = mod._warlock_outfits[unit]

	if outfit and Unit.alive(outfit) then
		pcall(func, outfit, index, value, ...)
	end

	return func(unit, index, value, ...)
end)

mod:hook(Unit, "animation_set_constraint_target", function(func, unit, index, value, ...)
	local outfit = mod._warlock_outfits[unit]

	if outfit and Unit.alive(outfit) then
		pcall(func, outfit, index, value, ...)
	end

	return func(unit, index, value, ...)
end)


-- Runtime material swap for the warlock body (Pusfume native contract).
-- The five boot-package wb_* materials are SDK compiles, which the engine can
-- only render RIGID and dark: the mod SDK never emits the character-skinning
-- shader permutation (vt2-pusfume issue #6). The real bindings are game child
-- payloads spliced over child_materials/warlock_bombardier/wb_*_child, which
-- ride in a separate NON-boot package (boot-flushing a spliced child crashes
-- the engine at PatchedResourcePackage::flush - v0.1.16). Swap every slot once
-- both packages are resident; the hook runs per spawn, so a miss self-heals
-- on the next bombardier.
local WARLOCK_DONOR_PACKAGE = "units/beings/player/dark_pact_skins/skaven_wind_globadier/skin_1001/third_person/chr_third_person_mesh"
local WARLOCK_CHILD_PACKAGE = "resource_packages/doomrocket/warlock_child"
local WARLOCK_SLOT_MATERIALS = {
	DoomRocket_Armor = "child_materials/warlock_bombardier/wb_armor_child",
	DoomRocket_Backpack = "child_materials/warlock_bombardier/wb_backpack_child",
	wb_skin = "child_materials/warlock_bombardier/wb_skin_child",
	wb_fur = "child_materials/warlock_bombardier/wb_fur_child",
	wb_whiskers = "child_materials/warlock_bombardier/wb_whiskers_child",
}
local warlock_child_package_requested = false

mod._apply_warlock_child_materials = function(outfit_unit)
	if not Managers.package:has_loaded(WARLOCK_DONOR_PACKAGE, "global") then
		printf("[doomrocket] warlock materials skipped: globadier donor package not resident yet")
		return
	end

	if not mod.load_package or not mod.package_status then
		printf("[doomrocket] warlock materials skipped: VMF package API unavailable")
		return
	end

	if not warlock_child_package_requested then
		warlock_child_package_requested = true
		mod:load_package(WARLOCK_CHILD_PACKAGE, nil, true)
	end

	if mod:package_status(WARLOCK_CHILD_PACKAGE) ~= "loaded" then
		printf("[doomrocket] warlock materials skipped: child package status %s",
			tostring(mod:package_status(WARLOCK_CHILD_PACKAGE)))
		return
	end

	for slot_name, material_path in pairs(WARLOCK_SLOT_MATERIALS) do
		Unit.set_material(outfit_unit, slot_name, material_path)
	end

	printf("[doomrocket] warlock child materials applied (5 slots)")
end

mod:hook(AIInventoryExtension, "_setup_configuration", function (func, self, unit, start_n, inventory_configuration, item_extension_init_data)
	-- Prune the armor bridge to nodes the OWNER actually has, BEFORE vanilla links.
	--
	-- vanilla link_unit does Unit.node(source, source_node), and a missing node is an
	-- engine-level fatal that pcall cannot catch, so the bridge may only name nodes that
	-- exist on this breed's base skeleton. Unit.has_node is the safe existence test.
	-- Pruning here (rather than shipping a hand-verified list) means we can name every
	-- bone the mesh is weighted to and let the ones the base lacks drop out quietly.
	mod._prune_armor_bridge(unit)

	local result = func(self, unit, start_n, inventory_configuration, item_extension_init_data)

	local outfit_units = self.inventory_item_outfit_units

	local is_mat_aval = Application.can_get('material', "     GvOtsyNy1'")

	local wearing_warlock_body = false

	for i, outfit_unit in ipairs(outfit_units) do
		if Unit.alive(outfit_unit) then
			local outfit_unit_name = Unit.get_data(outfit_unit, "unit_name")
			if outfit_unit_name == "units/beings/enemies/skaven_plague_monk/chr_skaven_plague_monk" then
				Unit.disable_animation_state_machine(outfit_unit)
			elseif outfit_unit_name == "units/warlock_bombardier/warlock_bombardier_3p" then
				-- This DCC-compiled unit's skin follows only its OWN animation system
				-- (v0.1.22 proved that path; v0.1.18-20 and v0.1.23 falsified
				-- scene-graph link driving with and without "transform" bone mode).
				-- The rig was authored to fit the gun rat's animation set, so: swap
				-- the unit onto the VANILLA ratling state machine (name-matched
				-- skeleton; clips resolve from the force-loaded ratling breed
				-- package) and let the Unit.animation_event mirror below replay the
				-- donor rat's events on it. Falls back to the unit's own baked idle
				-- SM if the swap is rejected.
				Unit.set_animation_bone_mode(outfit_unit, "transform")
				Unit.set_bones_lod(outfit_unit, 0)
				local swapped = pcall(set_animation_state_machine, outfit_unit,
					"units/beings/enemies/skaven_ratlinggunner/chr_skaven_ratlinggunner")
				Unit.enable_animation_state_machine(outfit_unit)
				if swapped then
					mod._warlock_outfits[unit] = outfit_unit
					printf("[doomrocket] warlock outfit on ratling state machine; mirroring anim events")
				else
					printf("[doomrocket] ratling state machine swap REJECTED; falling back to own idle")
					if Unit.has_animation_event(outfit_unit, "idle") then
						Unit.animation_event(outfit_unit, "idle")
					end
				end
				wearing_warlock_body = true
				mod._apply_warlock_child_materials(outfit_unit)
			elseif (outfit_unit_name == "units/bombadier/Backpack") and is_mat_aval then
				Unit.set_material(outfit_unit, 'lambert1', "     GvOtsyNy1'")
			end
		end
	end

	-- Crunch's unit now ships all five meshes (body, fur, vanilla armor, warlock armor,
	-- backpack), so the donor must not also draw. (An earlier `if false` here - staged
	-- when the set was believed body-less, then never reverted - shipped in v0.1.13 and
	-- resurrected the donor rat.)
	if wearing_warlock_body and Unit.alive(unit) then
		-- Hide the donor body's renderables only. Do NOT use Unit.set_unit_visibility on
		-- the owner: the outfit is linked to the owner's scene-graph nodes and driven by
		-- the owner's animation, so the base unit must keep animating even though nothing
		-- of it should draw.
		local hidden = 0

		-- v0.1.10-dev hid 0: the loop was gated on Unit.has_mesh(unit, index), but that
		-- API does not take a mesh index, so it returned false and broke immediately.
		-- Ask the unit how many meshes it has; fall back to the range the existing
		-- create_unit_extensions hook already writes to (it hides up to index 16, so
		-- those indices are known to exist on this donor).
		local num_meshes = 0
		local counted = pcall(function()
			num_meshes = Unit.num_meshes(unit)
		end)

		if not counted or not num_meshes or num_meshes <= 0 then
			num_meshes = 17
		end

		for mesh_index = 0, num_meshes - 1 do
			if pcall(Unit.set_mesh_visibility, unit, mesh_index, false, "default") then
				hidden = hidden + 1
			end
		end

		printf("[doomrocket] donor reports %s mesh(es)%s",
			tostring(num_meshes), counted and "" or " (Unit.num_meshes unavailable; used fallback)")

		printf("[doomrocket] warlock body attached; hid %d base mesh(es) on the donor unit", hidden)
	end

	local weapon_units = self.inventory_item_weapon_units

	for i, weapon_unit in ipairs(weapon_units) do
		if Unit.alive(weapon_unit) then
			local weapon_unit_name = Unit.get_data(weapon_unit, "unit_name")
			if (weapon_unit_name == "units/rocket/pRocketLauncher") and is_mat_aval then
				Unit.set_material(weapon_unit, 'lambert2', "     GvOtsyNy1'")
				Unit.set_material(weapon_unit, 'lambert3', "     GvOtsyNy1'")
			end
		end
	end

	return result
end)

-- these functions are needed so the client can properly spawn in the custom breed with right breed data set
local unit_go_sync_functions = require("scripts/mods/doomrocket/utils/game_object_initializers_extractors")
mod:hook(UnitSpawner, 'set_gameobject_initializer_data', function(func, self, initializer_function_table, extraction_function_table, gameobject_context)
	initializer_function_table = unit_go_sync_functions.initializers
	extraction_function_table = unit_go_sync_functions.extractors
	return func(self, initializer_function_table, extraction_function_table, gameobject_context)
end)

mod:hook(UnitSpawner, 'set_gameobject_to_unit_creator_function', function(func, self, function_table)
	function_table = unit_go_sync_functions.unit_from_gameobject_creator_func
	return func(self, function_table)
end)


--stops a crash but needs to be revisted as it borks other things
-- mod:hook(Unit, 'animation_set_constraint_target', function(func, self, index, value)

-- 	-- print(index)
-- 	-- print(value)

-- 	local result = func(self, index, value)

-- 	-- return func(self, index, value)
-- 	return
-- end)

-- Merge our two templates into the REAL vanilla table rather than swapping the whole
-- file out for a stale copy. See utils/unit_extension_template_additions.lua.
local apply_unit_extension_template_additions = dofile("scripts/mods/doomrocket/utils/unit_extension_template_additions")

mod:hook(_G, 'require', function(func, file_name, ...)
	local result = func(file_name, ...)

	if file_name == "scripts/network/unit_extension_templates" and type(result) == "table" then
		apply_unit_extension_template_additions(result)
	end

	return result
end)

-- unit_spawner.lua and breed_freezer.lua capture this table at file scope during boot,
-- before any mod loads, so the hook above would never reach those references. Merging
-- once directly covers them whenever require returns a cached table. Idempotent.
apply_unit_extension_template_additions(require("scripts/network/unit_extension_templates"))

-- print(Network.config_hash('global'))



-- local function get_network_options()
-- 	local network_options = {
-- 		config_file_name = "scripts/mods/doomrocket/utils/doomrocket", -- MODIFIED
-- 		ip_address = Network.default_network_address(),
-- 		lobby_port = GameSettingsDevelopment.network_port,
-- 		map = "None",
-- 		max_members = 4,
-- 		project_hash = "bulldozer",
-- 		query_port = script_data.query_port or script_data.settings.query_port,
-- 		server_port = script_data.server_port or script_data.settings.server_port or 27015,
-- 		steam_port = script_data.steam_port or script_data.settings.steam_port,
-- 	}
-- 	return network_options
-- end

-- mod:hook_origin(LobbyManager, "setup_network_options", function(self, increment_lobby_port)
-- 	local network_options = get_network_options()
-- 	local lobby_port = script_data.server_port or script_data.settings.server_port or network_options.lobby_port
-- 	lobby_port = lobby_port + self._lobby_port_increment
-- 	if increment_lobby_port then
-- 		self._lobby_port_increment = self._lobby_port_increment + 1
-- 	end
-- 	network_options.lobby_port = lobby_port
-- 	self._network_options = network_options
-- end)

mod:hook(PickupUnitExtension, 'init', function(func, self, extension_init_context, unit, extension_init_data)

	local interaction_type = Unit.get_data(unit, "interaction_data", "interaction_type")
	local result = func(self, extension_init_context, unit, extension_init_data)
	if interaction_type == "doom_rocket" then
		Unit.set_data(unit, "interaction_data", "interaction_type", "doom_rocket")
	end
	return result
end)


--for running projectile_rocket cleanup code only when rocket is marked for deletion
mod:hook(GrowQueue, 'pop_first', function(func, self)

	local unit = func(self)
	if unit then
		local prj_rckt = mod.projectiles[unit]
		if prj_rckt then
			prj_rckt:destroy()
		end
	end

	return unit
end)

-- Fatshark added a
-- assert(self.is_server, "[HealthTriggerSystem] Clients should not hold health trigger extensions")
-- line for some reason, no idea why. This just origin hooks it so it don't do that
mod:hook(HealthTriggerSystem,'extensions_ready', function (func, self, world, unit, extension_name)

	local extension = self.unit_extensions[unit]

	extension.health_extension = ScriptUnit.extension(unit, "health_system")

	assert(extension.health_extension)

	extension.last_health_percent = extension.health_extension:current_health_percent()
	extension.last_health_tick_percent = extension.health_extension:current_health_percent()
	extension.dialogue_input = ScriptUnit.extension_input(unit, "dialogue_system")
	extension.tick_time = 0
end)
