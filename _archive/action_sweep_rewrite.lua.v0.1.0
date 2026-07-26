local mod = get_mod("doomrocket")

ActionSweep = ActionSweep or {}

local unit_alive = Unit.alive
local unit_get_data = Unit.get_data
local unit_world_position = Unit.world_position
local unit_world_rotation = Unit.world_rotation
local unit_local_rotation = Unit.local_rotation
local unit_flow_event = Unit.flow_event
local unit_set_flow_variable = Unit.set_flow_variable
local unit_node = Unit.node
local unit_has_node = Unit.has_node
local unit_actor = Unit.actor
local unit_animation_event = Unit.animation_event
local unit_has_animation_event = Unit.has_animation_event
local unit_has_animation_state_machine = Unit.has_animation_state_machine
local actor_node = Actor.node
local action_hitbox_vertical_fov = math.degrees_to_radians(120)
local action_hitbox_horizontal_fov = math.degrees_to_radians(115.55)

local function weapon_printf(...)
	if script_data.debug_weapons then
		print("[ActionSweep] " .. sprintf(...))
	end
end

local BAKED_SWEEP_TIME = 1
local BAKED_SWEEP_POS = 2
local BAKED_SWEEP_ROT = 5

local function _get_baked_pose(time, data)
	local num_data = #data

	for i = 1, num_data, 1 do
		local current = data[i]
		local next = data[math.min(i + 1, num_data)]

		if current == next or (i == 1 and time <= current[BAKED_SWEEP_TIME]) then
			local loc = Vector3(current[BAKED_SWEEP_POS], current[BAKED_SWEEP_POS + 1], current[BAKED_SWEEP_POS + 2])
			local rot = Quaternion.from_elements(current[BAKED_SWEEP_ROT], current[BAKED_SWEEP_ROT + 1], current[BAKED_SWEEP_ROT + 2], current[BAKED_SWEEP_ROT + 3])

			return Matrix4x4.from_quaternion_position(rot, loc)
		elseif current[BAKED_SWEEP_TIME] <= time and time <= next[BAKED_SWEEP_TIME] then
			local time_range = math.max(next[BAKED_SWEEP_TIME] - current[BAKED_SWEEP_TIME], 0.0001)
			local lerp_t = (time - current[BAKED_SWEEP_TIME]) / time_range
			local start_position = Vector3(current[BAKED_SWEEP_POS], current[BAKED_SWEEP_POS + 1], current[BAKED_SWEEP_POS + 2])
			local start_rotation = Quaternion.from_elements(current[BAKED_SWEEP_ROT], current[BAKED_SWEEP_ROT + 1], current[BAKED_SWEEP_ROT + 2], current[BAKED_SWEEP_ROT + 3])
			local end_position = Vector3(next[BAKED_SWEEP_POS], next[BAKED_SWEEP_POS + 1], next[BAKED_SWEEP_POS + 2])
			local end_rotation = Quaternion.from_elements(next[BAKED_SWEEP_ROT], next[BAKED_SWEEP_ROT + 1], next[BAKED_SWEEP_ROT + 2], next[BAKED_SWEEP_ROT + 3])
			local current_position = Vector3.lerp(start_position, end_position, lerp_t)
			local current_rotation = Quaternion.lerp(start_rotation, end_rotation, lerp_t)

			return Matrix4x4.from_quaternion_position(current_rotation, current_position)
		end
	end

	return nil, nil
end

local function get_baked_data_name(action_hand)
	if action_hand then
		return "baked_sweep_" .. action_hand
	else
		return "baked_sweep"
	end
end

local sound_events = {
	javelin_stab_hit = "stab_hit",
	slashing_hit = "slashing_hit",
	stab_hit = "stab_hit",
	Play_weapon_fire_torch_flesh_hit = "burning_hit",
	hammer_2h_hit = "blunt_hit",
	axe_2h_hit = "slashing_hit",
	crowbill_stab_hit = "stab_hit",
	axe_1h_hit = "slashing_hit",
	blunt_hit = "blunt_hit"
}

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

ActionSweep._play_character_impact = function (self, is_server, attacker_unit, hit_unit, breed, hit_position, hit_zone_name, current_action, damage_profile, target_index, power_level, attack_direction, blocking, boost_curve_multiplier, is_critical_strike, backstab_multiplier)
	local attacker_player = Managers.player:owner(attacker_unit)
	local husk = attacker_player.bot_player
	local world = self.world
	local owner_unit = self.owner_unit
	local target_settings = (damage_profile.targets and damage_profile.targets[target_index]) or damage_profile.default_target
	local attack_template_name = target_settings.attack_template
	local attack_template = AttackTemplates[attack_template_name]
	local predicted_damage = 0
	local target_invulerable = false

	if target_settings then
		local damage_source = self.item_name
		local boost_curve = BoostCurves[target_settings.boost_curve_type]
		predicted_damage, target_invulerable = DamageUtils.calculate_damage(DamageOutput, hit_unit, attacker_unit, hit_zone_name, power_level, boost_curve, boost_curve_multiplier, is_critical_strike, damage_profile, target_index, backstab_multiplier, damage_source)
	end

	local no_damage = predicted_damage <= 0
	local hitzone_armor_categories = breed.hitzone_armor_categories
	local target_unit_armor = (hitzone_armor_categories and hitzone_armor_categories[hit_zone_name]) or breed.armor_category
	local sound_event = (no_damage and current_action.stagger_impact_sound_event) or current_action.impact_sound_event

	if blocking then
		if sound_events[sound_event] == "blunt_hit" then
			sound_event = breed.shield_blunt_block_sound or "blunt_hit_shield_wood"
		elseif sound_events[sound_event] == "slashing_hit" then
			sound_event = breed.shield_slashing_block_sound or "slashing_hit_shield_wood"
		elseif sound_events[sound_event] == "stab_hit" then
			sound_event = breed.shield_stab_block_sound or "stab_hit_shield_wood"
		elseif sound_events[sound_event] == "burning_hit" then
			sound_event = breed.shield_stab_block_sound or "Play_weapon_fire_torch_wood_shield_hit"
		end
	elseif target_unit_armor == 2 then
		sound_event = (no_damage and current_action.no_damage_impact_sound_event) or current_action.armor_impact_sound_event or current_action.impact_sound_event
	end

	local damage_type = "default"
	local hit_effect = nil

	if blocking then
		if target_unit_armor == 2 then
			hit_effect = "fx/hit_enemy_shield_metal"
		else
			hit_effect = "fx/hit_enemy_shield"
		end

		damage_type = "no_damage"
	elseif target_invulerable then
		hit_effect = "fx/hit_enemy_shield_metal"
	elseif not damage_type or damage_type == "no_damage" then
		hit_effect = current_action.no_damage_impact_particle_effect
	elseif predicted_damage <= 0 and target_unit_armor == 2 then
		hit_effect = current_action.armour_impact_particle_effect or "fx/hit_armored"
	elseif predicted_damage <= 0 then
		hit_effect = current_action.no_damage_impact_particle_effect
	elseif not breed.no_blood_splatter_on_damage then
		hit_effect = current_action.impact_particle_effect or BloodSettings:get_hit_effect_for_race(breed.race)

		EffectHelper.player_critical_hit(world, is_critical_strike, attacker_unit, hit_unit, hit_position)
	end

	local additional_hit_effects = current_action.additional_hit_effects
	local is_dummy = unit_get_data(hit_unit, "is_dummy")

	if additional_hit_effects and not is_dummy then
		for i = 1, #additional_hit_effects, 1 do
			EffectHelper.player_melee_hit_particles(world, additional_hit_effects[i], hit_position, attack_direction, damage_type, hit_unit, predicted_damage)
		end
	end

	if predicted_damage <= 0 then
		damage_type = "no_damage"
	end

	if hit_effect and not is_dummy then
		EffectHelper.player_melee_hit_particles(world, hit_effect, hit_position, attack_direction, damage_type, hit_unit, predicted_damage)
	end

	if (hit_zone_name == "head" or hit_zone_name == "neck") and attack_template.headshot_sound then
		sound_event = attack_template.headshot_sound
	end

	if target_invulerable then
		sound_event = "enemy_grudge_deflect"

		DamageUtils.handle_hit_indication(self.owner_unit, hit_unit, 0, hit_zone_name, false, true)
	end

	local sound_type = attack_template.sound_type

	if sound_event then
		if not sound_type then
			return
		end

		EffectHelper.play_melee_hit_effects(sound_event, world, hit_position, sound_type, husk, hit_unit)

		local network_manager = Managers.state.network
		local sound_event_id = NetworkLookup.sound_events[sound_event]
		local sound_type_id = NetworkLookup.melee_impact_sound_types[sound_type]
		local hit_unit_id = network_manager:unit_game_object_id(hit_unit)

		if is_server then
			network_manager.network_transmit:send_rpc_clients("rpc_play_melee_hit_effects", sound_event_id, hit_position, sound_type_id, hit_unit_id)
		else
			network_manager.network_transmit:send_rpc_server("rpc_play_melee_hit_effects", sound_event_id, hit_position, sound_type_id, hit_unit_id)
		end
	else
		Application.warning("[ActionSweep] Missing sound event for sweep action in unit %q.", self.weapon_unit)
	end

	local multiplier_type = DamageUtils.get_breed_damage_multiplier_type(breed, hit_zone_name, is_dummy)

	if (multiplier_type == "headshot" or (multiplier_type == "weakspot" and not blocking)) and not current_action.no_headshot_sound and unit_alive(hit_unit) then
		local first_person_extension = ScriptUnit.extension(owner_unit, "first_person_system")

		first_person_extension:play_hud_sound_event("Play_hud_melee_headshot", nil, false)
	end

	local on_hit_hud_sound_event = current_action.on_hit_hud_sound_event

	if on_hit_hud_sound_event then
		local first_person_extension = ScriptUnit.extension(owner_unit, "first_person_system")

		first_person_extension:play_hud_sound_event(on_hit_hud_sound_event, nil, false)
	end

	local target_health_extension = ScriptUnit.extension(hit_unit, "health_system")
	local wounds_left = target_health_extension:current_health()
	local target_presumed_dead = wounds_left <= predicted_damage
	local sound_effect_extension = ScriptUnit.has_extension(self.owner_unit, "sound_effect_system")

	if sound_effect_extension and target_presumed_dead then
		sound_effect_extension:melee_kill()
	end

	if blocking then
		return false
	end

	if not is_dummy and not husk and not target_presumed_dead and breed and not breed.disable_local_hit_reactions and unit_has_animation_state_machine(hit_unit) then
		local hit_anim = nil

		if unit_has_animation_event(hit_unit, "hit_reaction_climb") then
			local network_manager = Managers.state.network
			local hit_unit_id = network_manager:unit_game_object_id(hit_unit)
			local action_name = NetworkLookup.bt_action_names[GameSession.game_object_field(network_manager:game(), hit_unit_id, "bt_action_name")]

			if action_name and action_name == "climb" then
				hit_anim = "hit_reaction_climb"
			end
		end

		if not hit_anim then
			local hit_unit_dir = Quaternion.forward(unit_local_rotation(hit_unit, 0))
			local angle_difference = Vector3.flat_angle(hit_unit_dir, attack_direction)

			if angle_difference < -math.pi * 0.75 or angle_difference > math.pi * 0.75 then
				hit_anim = "hit_reaction_backward"
			elseif angle_difference < -math.pi * 0.25 then
				hit_anim = "hit_reaction_left"
			elseif angle_difference < math.pi * 0.25 then
				hit_anim = "hit_reaction_forward"
			else
				hit_anim = "hit_reaction_right"
			end
		end

        local breed = Unit.get_data(hit_unit, "breed")
        if breed then
            if breed.name == "skaven_doomrocket" then
                local swap_tisch = alt_events[hit_anim]
                if swap_tisch then
                    Unit.set_animation_state_machine(hit_unit, swap_tisch.machine)
                    hit_anim = swap_tisch.event
                    mod.anim_emitters[hit_unit]:update_animation(hit_unit, hit_anim)
                elseif not Unit.has_animation_event(hit_unit, hit_anim) then
                    Unit.set_animation_state_machine(hit_unit, "units/beings/enemies/skaven_ratlinggunner/chr_skaven_ratlinggunner")
                end
            end
        end
		unit_animation_event(hit_unit, hit_anim)
	end

	return target_presumed_dead
end