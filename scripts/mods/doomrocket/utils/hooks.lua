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
						-- NO state-machine swap: the ratling machine's clips animate
						-- gun bones the stormvermin skeleton lacks - binding it to
						-- this donor is a raw native crash moments after spawn
						-- (v0.1.34, no Error Context). Cross-skeleton SM binding is
						-- dead in EVERY direction now: mod->vanilla (v0.1.24,
						-- AnimationBlender assert) and vanilla->vanilla (v0.1.34).
						-- The donor keeps its own stormvermin machine; gun-rat
						-- clips require animations compiled against this skeleton.
						for animaiton_event, details in pairs(new_animations) do
							Unit.set_data(unit, animaiton_event, "timing", details.timing)
							Unit.set_data(unit, animaiton_event, "emitted_event", details.emitted_event)
						end

						mod.anim_emitters[unit] = AnimEmitter:new(unit, blackboard)

						-- The fixed-index hides that lived here targeted the RATLING
						-- body's gun/tank/belt LOD meshes; on the stormvermin donor
						-- those indices are arbitrary (and an out-of-range index is
						-- an engine assert). The full donor hide runs at warlock
						-- attach in the _setup_configuration hook below.
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
mod._warlock_donor_mesh_counts = mod._warlock_donor_mesh_counts or setmetatable({}, { __mode = "k" })

local function set_warlock_donor_mesh_visibility(owner_unit, visible, reason)
	if not owner_unit or not Unit.alive(owner_unit) then
		return false
	end

	local num_meshes = mod._warlock_donor_mesh_counts[owner_unit]
	if not num_meshes then
		local counted = pcall(function()
			num_meshes = Unit.num_meshes(owner_unit)
		end)

		if not counted or not num_meshes or num_meshes <= 0 then
			num_meshes = 17
		end

		mod._warlock_donor_mesh_counts[owner_unit] = num_meshes
	end

	local changed = 0
	for mesh_index = 0, num_meshes - 1 do
		if pcall(Unit.set_mesh_visibility, owner_unit, mesh_index, visible, "default") then
			changed = changed + 1
		end
	end

	printf("[doomrocket:RAGDOLL] donor fallback visibility=%s meshes=%d/%d reason=%s",
		tostring(visible), changed, num_meshes, tostring(reason))

	return changed > 0
end

mod:hook(Unit, "animation_event", function(func, unit, event, ...)
	-- The doomrocket donor is a STORMVERMIN body whose machine lacks the gun
	-- rat's event vocabulary (attack_shoot_*, wind_up_*). DO NOT hot-swap it
	-- onto the ratling machine: cross-skeleton state-machine binding is a raw
	-- native crash (v0.1.34) - the clips animate bones this skeleton lacks.
	-- Unknown events are swallowed instead; the visual for those actions stays
	-- whatever the stormvermin machine is doing until clips compiled against
	-- this skeleton exist.
	local breed = unit_get_data(unit, "breed")

	if breed and breed.name == "skaven_doomrocket" and not has_animation_event(unit, event) then
		return
	end

	-- Mirror registry (self-ASM driving mode only; empty in bridge mode).
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

-- NO raw-index animation mirroring. v0.1.25 crash: the rat's aim system
-- called animation_set_constraint_target(rat, 0, aim_target); forwarding that
-- raw index to the outfit - whose own state machine has no constraints - is
-- an engine assert that pcall CANNOT catch (same uncatchable class as the
-- v0.1.24 AnimationBlender crash). Variable and constraint indices are only
-- meaningful within one compiled state machine. If our SM ever needs
-- variable/aim mirroring, it must translate by NAME (capture the rat's
-- animation_find_variable name->index calls, re-find on the outfit), never
-- by index. Events are mirrored above because they are name-based and gated
-- on Unit.has_animation_event.


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
	{ "DoomRocket_Armor", "child_materials/warlock_bombardier/wb_armor_child" },
	{ "DoomRocket_Backpack", "child_materials/warlock_bombardier/wb_backpack_child" },
	{ "wb_skin", "child_materials/warlock_bombardier/wb_skin_child" },
	{ "wb_fur", "child_materials/warlock_bombardier/wb_fur_child" },
	{ "wb_whiskers", "child_materials/warlock_bombardier/wb_whiskers_child" },
}
local WARLOCK_CUSTOM_TEXTURES = {
	"textures/warlock_bombardier/wb_armor_df",
	"textures/warlock_bombardier/wb_armor_nm",
	"textures/warlock_bombardier/wb_backpack_df",
	"textures/warlock_bombardier/wb_backpack_e",
	"textures/warlock_bombardier/wb_backpack_nm",
	"textures/warlock_bombardier/wb_skin_df",
	"textures/warlock_bombardier/wb_skin_nm",
	"textures/warlock_bombardier/wb_whiskers_df",
}
local warlock_child_package_requested = false

-- v0.1.43 proved that "keep the custom actors kinematic" was insufficient.
-- The owner's death event was mirrored into the outfit before the delayed
-- handoff; the outfit's ragdoll state then made its actors dynamic internally,
-- stalling physics for 1-1.6 s and corrupting the skeleton before Lua ran
-- again. v0.1.44 removes the custom PhysX scene and ragdoll layer altogether.
--
-- v0.1.44 then proved that a native carrier alone is not enough: linking 97
-- target bones independently with World.link_unit destroys this Blender-built
-- mesh's local scene-graph hierarchy and recreates the old "stick figure".
--
-- Keep the existing root-only attachment. This function is called BEFORE
-- ai_extension:die sends the owner's death event; it detaches event mirroring,
-- keeps the outfit ASM live for render evaluation, and builds an index-pair
-- driver. The death reaction copies each vanilla carrier LOCAL rotation into
-- the equivalent node of the intact outfit hierarchy every frame. This is the
-- runtime analogue of the parent-relative retarget that made the living
-- v0.1.39 animation set work.
mod._prepare_warlock_death = function(owner_unit, source)
	local outfit_unit = mod._warlock_outfits[owner_unit]

	if not outfit_unit or not Unit.alive(outfit_unit) then
		printf("[doomrocket:RAGDOLL] %s death: no live warlock outfit to hand off",
			tostring(source))
		return
	end

	-- Remove the mirror entry before the owner's death event so that event is not
	-- forwarded into the outfit. v0.1.48 disabled the outfit ASM here; six clean
	-- v0.1.48 deaths left the native carrier (and embedded arrows) in place while
	-- the entire skinned outfit vanished. Keep the outfit's own ASM evaluating so
	-- Stingray continues to update its skinned render state/bounds, then apply the
	-- carrier rotations after the living mirror has been detached.
	mod._warlock_outfits[owner_unit] = nil
	Unit.set_animation_bone_mode(outfit_unit, "transform")
	Unit.set_bones_lod(outfit_unit, 0)
	Unit.set_unit_visibility(outfit_unit, true)

	-- Always expose the native carrier at death. It is the actual stable PhysX
	-- ragdoll and forms a fail-safe underlay if the custom skinned overlay is
	-- culled or transformed away. This is deliberately death-only: the donor
	-- remains hidden while alive, and the custom outfit remains enabled above it.
	set_warlock_donor_mesh_visibility(owner_unit, true, "death-underlay")

	-- v0.1.48: ROTATION-ONLY retarget. Copying full local poses (v0.1.45-47)
	-- resurrected the closed v0.1.28 bridge failure at death time: the ratling
	-- carrier's local matrices carry ITS bone translations and its animated
	-- proportion SCALE (the *_scale bones the bridge maps), which compound
	-- multiplicatively down every chain on Crunch's hierarchy - the reported
	-- giant sky-flying stretch. Rotations alone cannot stretch: bone lengths
	-- and proportions stay at the outfit's own bind. j_hips additionally
	-- copies local TRANSLATION (one root-relative bone, no chain to compound)
	-- so the corpse actually falls to the ground instead of pivoting in air.
	-- *_scale bones and the aim_target constraint node are excluded outright.
	local bridge = AttachmentNodeLinking.doomrocket_warlock_bridge
	local node_pairs = {}
	local skipped = 0
	for i = 1, #bridge do
		local entry = bridge[i]
		local target_node = entry.target
		local source_node = entry.source
		local target_name = type(target_node) == "string" and target_node or nil
		local source_name = type(source_node) == "string" and source_node or nil
		local excluded =
			(target_name and (target_name:sub(-6) == "_scale" or target_name == "aim_target")) or
			(source_name and (source_name:sub(-6) == "_scale" or source_name == "aim_target"))

		-- Target 0 is already root-linked by the inventory attachment. Preserve
		-- that one link and drive only child-node local rotations.
		if target_node ~= 0 and not excluded then
			local target_index = target_name and
				Unit.node(outfit_unit, target_name) or target_node
			local source_index = source_name and
				Unit.node(owner_unit, source_name) or source_node

			node_pairs[#node_pairs + 1] = {
				target = target_index,
				source = source_index,
				is_hips = (source_name == "j_hips") or (target_name == "j_hips"),
			}
		elseif target_node ~= 0 then
			skipped = skipped + 1
		end
	end

	local driver = {
		owner = owner_unit,
		outfit = outfit_unit,
		node_pairs = node_pairs,
		owner_hips = Unit.node(owner_unit, "j_hips"),
		outfit_hips = Unit.node(outfit_unit, "j_hips"),
		frame = 0,
		escape_reported = false,
	}

	for i = 1, #node_pairs do
		local pair = node_pairs[i]
		Unit.set_local_rotation(outfit_unit, pair.target,
			Unit.local_rotation(owner_unit, pair.source))
		if pair.is_hips then
			Unit.set_local_position(outfit_unit, pair.target,
				Unit.local_position(owner_unit, pair.source))
		end
	end

	local owner_root = Unit.world_position(owner_unit, 0)
	local outfit_root = Unit.world_position(outfit_unit, 0)
	local owner_hips = Unit.world_position(owner_unit, driver.owner_hips)
	local outfit_hips = Unit.world_position(outfit_unit, driver.outfit_hips)
	printf("[doomrocket:RAGDOLL] %s pre-event live-ASM rotation carrier active: nodes=%d scale/aim_excluded=%d custom_physics=absent root_delta=%.3f hips_delta=%.3f",
		tostring(source), #node_pairs, skipped,
		Vector3.length(outfit_root - owner_root), Vector3.length(outfit_hips - owner_hips))

	return driver
end

mod._update_warlock_death_pose = function(data)
	local driver = data.warlock_pose_driver

	if not driver then
		return
	end

	local owner_unit = driver.owner
	local outfit_unit = driver.outfit

	if not owner_unit or not Unit.alive(owner_unit) or
			not outfit_unit or not Unit.alive(outfit_unit) then
		if owner_unit and Unit.alive(owner_unit) then
			set_warlock_donor_mesh_visibility(owner_unit, true, "outfit-not-alive")
		end
		printf("[doomrocket:RAGDOLL] pose driver stopped owner_alive=%s outfit_alive=%s frame=%d",
			tostring(owner_unit and Unit.alive(owner_unit) or false),
			tostring(outfit_unit and Unit.alive(outfit_unit) or false),
			driver.frame or -1)
		data.warlock_pose_driver = nil
		return
	end

	driver.frame = driver.frame + 1

	local node_pairs = driver.node_pairs
	for i = 1, #node_pairs do
		local pair = node_pairs[i]
		Unit.set_local_rotation(outfit_unit, pair.target,
			Unit.local_rotation(owner_unit, pair.source))
		if pair.is_hips then
			Unit.set_local_position(outfit_unit, pair.target,
				Unit.local_position(owner_unit, pair.source))
		end
	end

	local frame = driver.frame
	if frame == 1 or frame == 2 or frame == 4 or frame == 8 or
			frame == 16 or frame == 32 or frame == 64 then
		-- Reassert custom-overlay visibility at diagnostic checkpoints. This also
		-- defeats any death flow that merely toggles the outfit visibility flag.
		Unit.set_unit_visibility(outfit_unit, true)

		local owner_root = Unit.world_position(owner_unit, 0)
		local outfit_root = Unit.world_position(outfit_unit, 0)
		local owner_hips = Unit.world_position(owner_unit, driver.owner_hips)
		local outfit_hips = Unit.world_position(outfit_unit, driver.outfit_hips)
		local root_delta = Vector3.length(outfit_root - owner_root)
		local hips_delta = Vector3.length(outfit_hips - owner_hips)

		printf("[doomrocket:RAGDOLL] sample frame=%d owner_alive=true outfit_alive=true root_delta=%.3f hips_delta=%.3f",
			frame, root_delta, hips_delta)

		if not driver.escape_reported and (root_delta > 5 or hips_delta > 5) then
			driver.escape_reported = true
			set_warlock_donor_mesh_visibility(owner_unit, true, "overlay-transform-escape")
			printf("[doomrocket:RAGDOLL] overlay transform escaped carrier frame=%d root_delta=%.3f hips_delta=%.3f",
				frame, root_delta, hips_delta)
		end
	end
end

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

	local missing_textures = 0
	for _, texture_path in ipairs(WARLOCK_CUSTOM_TEXTURES) do
		if not Application.can_get("texture", texture_path) then
			missing_textures = missing_textures + 1
			printf("[doomrocket:MATERIAL] texture NOT resident: %s", texture_path)
		end
	end

	local applied = 0
	for _, binding in ipairs(WARLOCK_SLOT_MATERIALS) do
		local slot_name, material_path = binding[1], binding[2]
		if Application.can_get("material", material_path) then
			Unit.set_material(outfit_unit, slot_name, material_path)
			applied = applied + 1
			printf("[doomrocket:MATERIAL] slot %s <- %s", slot_name, material_path)
		else
			printf("[doomrocket:MATERIAL] material NOT resident for slot %s: %s",
				slot_name, material_path)
		end
	end

	printf("[doomrocket:MATERIAL] assignment summary: slots=%d/%d custom_textures=%d/%d resident",
		applied, #WARLOCK_SLOT_MATERIALS,
		#WARLOCK_CUSTOM_TEXTURES - missing_textures, #WARLOCK_CUSTOM_TEXTURES)
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
				-- Since v0.1.27 the unit compiles on DALO's recovered vanilla
				-- skeleton with vanilla asset conventions, so it is driven exactly
				-- like the plague-monk overlay: per-bone bridge links from the
				-- donor rat (playing vanilla ratling animations), own state machine
				-- DISABLED so the links win. The v0.1.18-23 stick figures came from
				-- compiling on Crunch's Blender-native armature, not from the
				-- bridge. Bone mode + LOD set first, per the Pusfume contract.
				--
				-- Still true (v0.1.24 crash): NEVER point this unit at a vanilla
				-- state machine - uncatchable AnimationBlender assert one frame
				-- later.
				-- SELF-ANIMATION (v0.1.37, the only configuration ever confirmed
				-- correct in-game - v0.1.22). Bridge driving is CLOSED: two
				-- compiles x two donors x scale-links on/off all deformed
				-- (v0.1.23/28/35/36); the engine's linked-skinning bind space is
				-- not producible from Blender FBX export. Gun-rat clips arrive by
				-- importing the ratling's compiled animations onto this rig via
				-- the Bitsquid tools (the path that produced the working idle)
				-- and compiling them against THIS skeleton.
				Unit.set_animation_bone_mode(outfit_unit, "transform")
				Unit.set_bones_lod(outfit_unit, 0)
				Unit.enable_animation_state_machine(outfit_unit)
				if Unit.has_animation_event(outfit_unit, "idle") then
					Unit.animation_event(outfit_unit, "idle")
				end
				mod._warlock_outfits[unit] = outfit_unit
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

		mod._warlock_donor_mesh_counts[unit] = num_meshes

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
