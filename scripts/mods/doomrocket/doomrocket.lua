local mod = get_mod("doomrocket")
-- Your mod code goes here.
-- https://vmf-docs.verminti.de

local MOD_VERSION = "0.1.0-dev"
printf("[doomrocket:LOAD] v%s", MOD_VERSION)

-- mod:dofile("scripts/mods/doomrocket/utils/LobbyManager")
-- Managers.lobby = ModLobbyManager:new()


Managers.package:load("resource_packages/breeds/skaven_ratling_gunner", "global")
-- Managers.package:load("resource_packages/breeds/skaven_warpfire_thrower", "global")

mod:dofile("scripts/mods/doomrocket/breeds/skaven_doomrocket")
mod:dofile("scripts/mods/doomrocket/interactions/doom_rocket_interaction")
mod:dofile("scripts/mods/doomrocket/interactions/doom_rocket_pickup")
mod:dofile("scripts/mods/doomrocket/extensions/projectile_rocket")
mod:dofile("scripts/mods/doomrocket/extensions/anim_emitter")
local threat_values = {}

for breed_name, data in pairs(Breeds) do
	threat_values[breed_name] = override_threat_value or data.threat_value or 0

	if not data.threat_value then
		ferror("missing threat in breed %s", breed_name)
	end
end
ConflictDirector.calculate_threat_value = function (self)
	local threat_value = 0
	local i = 0
	local activated_per_breed = Managers.state.performance:activated_per_breed()

	for breed_name, amount in pairs(activated_per_breed) do
		threat_value = threat_value + threat_values[breed_name] * amount
		i = i + amount
	end

	self.delay_horde = self.delay_horde_threat_value < threat_value
	self.delay_mini_patrol = self.delay_mini_patrol_threat_value < threat_value
	self.delay_specials = self.delay_specials_threat_value < threat_value
	self.threat_value = threat_value
	self.num_aggroed = i
end

mod:dofile("scripts/mods/doomrocket/behavior/nodes/skaven_doomrocket/generated/bt_selector_skaven_doomrocket")
mod:dofile("scripts/mods/doomrocket/behavior/nodes/skaven_doomrocket/bt_doomrocket_launch_action")
mod:dofile("scripts/mods/doomrocket/behavior/nodes/skaven_doomrocket/bt_doomrocket_reload_action")
mod:dofile("scripts/mods/doomrocket/behavior/nodes/skaven_doomrocket/trees/skaven/skaven_doomrocket_behavior")
mod:dofile("scripts/mods/doomrocket/extensions/doomrocket_aim_template")
mod:dofile("scripts/mods/doomrocket/extensions/death_reactions")
mod:dofile("scripts/mods/doomrocket/utils/hooks")
mod:dofile("scripts/mods/doomrocket/utils/GameNetworkManager_utils")
mod:dofile("scripts/mods/doomrocket/rpc")
-- -- mod:dofile("scripts/managers/conflict_director/conflict_director")


--adds doomrocket killfeed icon
UISettings.breed_textures['skaven_doomrocket'] = 'unit_frame_portrait_enemy_doomrocket'

--setup rocket explosion template
ExplosionTemplates["doomrocket_explosion"] = {
	explosion = {
		radius =  6,
		alert_enemies = true,
		max_damage_radius = 1.5,
		always_hurt_players = true,
		alert_enemies_radius = 15,
		sound_event_name = "Play_enemy_combat_warpfire_backpack_explode",
		damage_profile = "warpfire_thrower_explosion",
		effect_name = "fx/chr_warp_fire_explosion_01",
		damage_type = "grenade",
		catapult_force = 10,
		catapult_players = true,
		dont_rotate_fx = true,
		allow_friendly_fire_override = true,
		player_push_speed = 15,
		ai_friendly_fire = true,
		difficulty_power_level = {
			easy = {
				power_level_glance = 400,
				power_level = 800
			},
			normal = {
				power_level_glance = 400,
				power_level = 800
			},
			hard = {
				power_level_glance = 400,
				power_level = 800
			},
			harder = {
				power_level_glance = 400,
				power_level = 800
			},
			hardest = {
				power_level_glance = 400,
				power_level = 800
			},
			cataclysm = {
				power_level_glance = 400,
				power_level = 800
			},
			cataclysm_2 = {
				power_level_glance = 400,
				power_level = 800
			},
			cataclysm_3 = {
				power_level_glance = 400,
				power_level = 800
			}
		},
	}
}

-- ExplosionTemplates["doomrocket_explosion"].explosion["damage_type"] = "kinetic"
ExplosionTemplates["doomrocket_explosion"].name = "doomrocket_explosion"

local num_explosions = #NetworkLookup.explosion_templates
NetworkLookup.explosion_templates[num_explosions + 1] = "doomrocket_explosion"
NetworkLookup.explosion_templates["doomrocket_explosion"] = num_explosions + 1




-- local function create_lookups(lookup, hashtable)
-- 	local i = #lookup

-- 	for key, _ in pairs(hashtable) do
-- 		i = i + 1
-- 		lookup[i] = key
-- 	end

-- 	return lookup
-- end
-- NetworkLookup.breeds = create_lookups({}, Breeds)

local num_breeeds = #NetworkLookup.breeds
NetworkLookup.breeds[num_breeeds + 1] = "skaven_doomrocket"
NetworkLookup.breeds["skaven_doomrocket"] = num_breeeds + 1

-- for k,v in pairs(NetworkLookup.breeds) do
-- 	mod:echo(k.."	"..tostring(v))
-- end

local num_dam = #NetworkLookup.damage_sources + 1
NetworkLookup.damage_sources["skaven_doomrocket"] = num_dam
NetworkLookup.damage_sources[num_dam] = "skaven_doomrocket"


local spawn_mod = get_mod("CreatureSpawner")

-- local add_spawn_catagory = {
--     beastmen_nu_gor = {
--         "misc",
--     },
--     beastmen_slaangor_standard = {
--         "misc",
--     },
-- }
-- table.merge(spawn_mod.unit_categories, table)
new_breed_names = {
    'skaven_doomrocket',
}

if spawn_mod then
	for i,breed_name in ipairs(new_breed_names) do
		table.insert(spawn_mod["all_units"], breed_name)
	end
end
mod:echo("done")

for bt_name, bt_node in pairs(BreedBehaviors) do
    bt_node[1] = "BTSelector_" .. bt_name
    bt_node.name = bt_name .. "_GENERATED"
end

local num_acitons = #NetworkLookup.bt_action_names
NetworkLookup.bt_action_names["fire_rocket"] = num_acitons
NetworkLookup.bt_action_names[num_acitons] = "fire_rocket"

local husk_num = #NetworkLookup.husks
NetworkLookup.husks[husk_num + 1] = "units/rocket/SM_Rocket"
NetworkLookup.husks["units/rocket/SM_Rocket"] = husk_num + 1

local num_anims = #NetworkLookup.anims
NetworkLookup.anims[num_anims + 1] = "doomrocket_reload"
NetworkLookup.anims["doomrocket_reload"] = num_anims + 1


mod.anim_emitters = {}
mod.projectiles = {}

function mod.update(dt)
    for unit_string,projectile in pairs(mod.projectiles) do
		if unit_string then
			projectile:update(dt)
		end
	end

	for unit,anim_emitter in pairs(mod.anim_emitters) do
		anim_emitter:update(unit, dt)
	end
end

mod:dofile("scripts/settings/breeds")


mod:dofile("scripts/mods/doomrocket/utils/action_sweep_rewrite")

mod.doom = false
mod:command("doom", "", function()
	if mod.doom then
		for setting_name, settings in pairs(SpecialsSettings) do
			if settings.breeds then
				for index, breed_name in ipairs(settings.breeds) do
					if breed_name == "skaven_doomrocket" then
						settings.breeds[index] = nil
					end
				end
			end
			if settings.difficulty_overrides then
				for diff, diff_settings in pairs(settings.difficulty_overrides) do
					for index, breed_name in ipairs(diff_settings) do
						if breed_name == "skaven_doomrocket" then
							diff_settings.breeds[index] = nil
						end
					end
				end
			end
		end
		mod.doom = false
	else
		for setting_name, settings in pairs(SpecialsSettings) do
			if settings.breeds then
				settings.breeds[#settings.breeds + 1] = "skaven_doomrocket"
			end
			if settings.difficulty_overrides then
				for diff, diff_settings in pairs(settings.difficulty_overrides) do
					if diff_settings.breeds then
						diff_settings.breeds[#diff_settings.breeds + 1] = "skaven_doomrocket"
					end
				end
			end
		end
		mod.doom = true
	end
	mod:chat_broadcast("Doom:	"..tostring(mod.doom))
end)

mod:hook(ConflictDirector, 'refresh_conflict_director_patches', function (func, self)
	local result = func(self)
	if mod.doom then
		if CurrentSpecialsSettings.breeds then
			local has_doomrockets = false
			for k,v in pairs(CurrentSpecialsSettings.breeds) do
				if k == 'skaven_doomrocket' or v == 'skaven_doomrocket' then
					has_doomrockets = true
				end
			end

			if not has_doomrockets then
				CurrentSpecialsSettings.breeds[#CurrentSpecialsSettings + 1] = 'skaven_doomrocket'
			end
		end
	end
	return result
end)

-- for setting_name, settings in pairs(SpecialsSettings) do
-- 	if settings.breeds then
-- 		for index, breed in ipairs(settings.breeds) do
-- 			mod:echo(tostring(index).." "..tostring(breed))
-- 		end
-- 	end
-- end

-- Managers.state.conflict.specials_pacing

-- for index, breed in ipairs(SpecialsSettings.skaven_light.breeds) do
-- 	mod:echo(tostring(index).." "..tostring(breed))
-- end

-- for setting_name, settings in pairs(SpecialsSettings) do
-- 	if settings.breeds then
-- 		settings.breeds[#settings.breeds + 1] = "skaven_doomrocket"
-- 	end
-- 	if settings.difficulty_overrides then
-- 		for diff, diff_settings in pairs(settings.difficulty_overrides) do
-- 			if diff_settings.breeds then
-- 				diff_settings.breeds[#diff_settings.breeds + 1] = "skaven_doomrocket"
-- 			end
-- 		end
-- 	end
-- end

-- for k,v in pairs(CurrentPacing) do
-- 	mod:echo(tostring(k).."	"..tostring(v))
-- end
-- mod:echo(CurrentPacing)
-- mod:echo(Managers.state.conflict.current_conflict_settings)
-- mod:echo(Managers.level_transition_handler:get_current_conflict_director())


-- for k,v in pairs(CurrentSpecialsSettings.breeds) do
-- 	mod:echo(tostring(k).."	"..tostring(v))
-- end

-- CurrentSpecialsSettings.breeds[#CurrentSpecialsSettings + 1] = 'skaven_doomrocket'

-- mod:hook(SpecialsPacing, 'update', function(func, self, t, alive_specials, specials_population, player_positions)
-- 	-- for k,v in pairs(self._specials_spawn_queue) do
-- 	-- 	mod:echo(tostring(k).."	"..tostring(v))
-- 	-- end
-- 	return func(self, t, alive_specials, specials_population, player_positions)
-- end)

-- local difficulty, difficulty_tweak = Managers.state.difficulty:get_difficulty()
-- local fallback_difficulty = Managers.state.difficulty.fallback_difficulty
-- local composition_difficulty = DifficultyTweak.converters.composition(difficulty, difficulty_tweak)
-- local director = ConflictDirectors[Managers.state.conflict.current_conflict_settings]
-- -- for k,v in pairs(director.specials) do
-- -- 	mod:echo(tostring(k).."	"..tostring(v))
-- -- end

-- -- local thinger = ConflictUtils.patch_settings_with_difficulty(table.clone(director.specials), composition_difficulty, fallback_difficulty)
-- local source_settings = table.clone(director.specials)
-- local overrides = source_settings.difficulty_overrides
-- local override_settings = overrides and (overrides[difficulty] or overrides[fallback_difficulty])

-- if override_settings then
-- 	for key, _ in pairs(source_settings) do
-- 		if key ~= "difficulty_overrides" then
-- 			source_settings[key] = override_settings[key] or source_settings[key]
-- 			mod:echo('not key')
-- 		end
-- 	end

-- 	source_settings.difficulty_overrides = nil

-- 	-- return source_settings
-- 	mod:echo('this branch')
-- else
-- 	-- return source_settings
-- 	mod:echo('that branch')
-- end

-- CurrentSpecialsSettings.breeds[#CurrentSpecialsSettings + 1] = 'skaven_doomrocket'
-- Managers.state.conflict:refresh_conflict_director_patches()

-- mod:hook(ConflictUtils, 'patch_settings_with_difficulty', function(func, source_settings, difficulty, fallback_difficulty)

-- 	return func(source_settings, difficulty, fallback_difficulty)
-- end)