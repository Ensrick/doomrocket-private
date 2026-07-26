local mod = get_mod("doomrocket")

local math_abs = math.abs
local math_log = math.log
local math_ex = math.exp
local math_pow = math.pow

local function radians_to_quaternion(theta, ro, phi)
    local c1 =  math.cos(theta/2)
    local c2 = math.cos(ro/2)
    local c3 = math.cos(phi/2)
    local s1 = math.sin(theta/2)
    local s2 = math.sin(ro/2)
    local s3 = math.sin(phi/2)
    local x = (s1*s2*c3) + (c1*c2*s3)
    local y = (s1*c2*c3) + (c1*s2*s3)
    local z = (c1*s2*c3) - (s1*c2*s3)
    local w = (c1*c2*c3) - (s1*s2*s3)
    local rot = Quaternion.from_elements(x, y, z, w)
    return rot
end

local function sign(x)
    return x>0 and 1 or x<0 and -1 or 0
end

local magnitude = Vector3.length
local dot_product = Vector3.dot
local normalize = Vector3.normal
local vec_dsit = Vector3.distance

local velocity = Actor.velocity
local pos_actor = Actor.position
local rot_actor = Actor.rotation
local rotate_actor = Actor.teleport_rotation
local actor_add_vel = Actor.add_velocity

local move_particles = World.move_particles
local vector4_multi = Quaternion.multiply
local quat_look = Quaternion.look

local trigger_audio = WwiseWorld.trigger_event
local stop_audio = WwiseWorld.stop_event

local rotate_unit = Unit.set_local_rotation
local unit_delta_rotation = Unit.delta_rotation

local linear_sphere_sweep = stingray.PhysicsWorld.linear_sphere_sweep

ProjectileRocket = class(ProjectileRocket)

ProjectileRocket.init = function (self, unit, attacker_unit, target_pos)
    Managers.package:load("resource_packages/breeds/skaven_warpfire_thrower", "global")
    self.unit_string = tostring(unit)
    self.unit = unit
    local actor = Unit.actor(unit, "throw")
    self.actor = actor
    self.target_z = target_pos.z
    self.target_y = target_pos.y
    self.target_x = target_pos.x
    self.attacker_unit = attacker_unit
    self.launch_z = Unit.local_position(self.attacker_unit, 0).z
    self.launch_y = Unit.local_position(self.attacker_unit, 0).y
    self.launch_x = Unit.local_position(self.attacker_unit, 0).x

    self.reached_apogee = false

    self.world = Unit.world(unit)
    local position = Actor.position(actor)
    local rotation = Actor.rotation(actor)
    self.exhaust_id = World.create_particles(self.world, "fx/chr_warp_fire_flamethrower_01", position, rotation, Vector3(0,0,1))

    self.physics_world = World.physics_world(self.world)

    self.wwise_world = Wwise.wwise_world(self.world)
    -- self.exhaust_sound_id = WwiseWorld.trigger_event(self.wwise_world, "Play_enemy_warpfire_thrower_shoot",  unit)
    -- local wwise_source, wwise_world = WwiseUtils.make_unit_auto_source(self.world, unit)
    local wwise_source = WwiseWorld.make_auto_source(self.wwise_world, unit)
    local playing_id = WwiseWorld.trigger_event(self.wwise_world, "Play_enemy_warpfire_thrower_shoot", true, wwise_source)
    WwiseWorld.set_source_parameter(self.wwise_world, wwise_source, "ratling_gun_shooting_loop_parameter", 0)

    self.wwise_source_id = wwise_source
    self.exhaust_sound_id = playing_id

    self.time_pass = 0

    self.attacker_goid = Managers.state.unit_storage:go_id(self.attacker_unit)

    self.exploded = false

end

ProjectileRocket.update = function (self, dt)
    if not Unit.alive(self.unit) then
        self:rocket_explode()
    end

    if self.actor and not self.exploded then
        local vel = velocity(self.actor)
        local speed = magnitude(vel)

        local new_direction = vel.x*vel.y*vel.z
        new_direction = new_direction/math.abs(new_direction)

        if not self.current_direction then
            self.current_direction = new_direction
        end

        self:straighten_rocket(vel)
        self:move_particles(self.actor)

        -- The rocket is ballistic now (see ROCKET in bt_doomrocket_launch_action), so a
        -- slow high lob is nearly stationary in Z at the top of its arc. The old
        -- `speed < 4` test would detonate it in mid-air there. Detonate only on a real
        -- stop (impact), and only after it has cleared the muzzle.
        if self.time_pass > 0.35 and speed < 1.5 then
            self:rocket_explode()
        end

        self.time_pass = self.time_pass + dt
        self.current_direction = new_direction
        self.previous_speed = speed
    end
end

ProjectileRocket.straighten_rocket = function(self, direction)
    local new_rotation = quat_look(direction)
    rotate_unit(self.unit, 0 , new_rotation)
    rotate_actor(self.actor, new_rotation)
end

-- No longer called from update. Kept for reference only.
--
-- This applied a one-frame upward kick at launch: exp(-500 * t^2) decays to ~0.7% by
-- t = 0.1s, so it was a Dirac-style impulse rather than sustained thrust. It was also
-- unreliable: `math.random(0.75, 1)` hits Lua 5.1's integer path and evaluates as
-- math.random(0, 1), so the kick was multiplied by ZERO on roughly half of all shots,
-- producing a flat dart. The arc now comes from a solved ballistic launch velocity, so
-- every shot lobs identically and predictably, which is what makes it dodgeable.
ProjectileRocket.guide_force = function(self, dt)
    return
end

ProjectileRocket.move_particles = function(self, actor)
    local pos = pos_actor(actor)
    local rot = vector4_multi(rot_actor(actor), radians_to_quaternion(0,0, math.pi))
    move_particles(self.world, self.exhaust_id, pos, rot)
end

ProjectileRocket.update_sounds = function(self)
    if self.time_pass > 2 then
        local pos = pos_actor(self.actor)
        local rot = vector4_multi(rot_actor(self.actor), radians_to_quaternion(0,0, math.pi))
        WwiseWorld.stop_event(self.wwise_world, self.exhaust_sound_id)
        self.exhaust_sound_id = WwiseWorld.trigger_event(self.wwise_world, "Play_enemy_warpfire_thrower_shoot",  pos, rot)
    end

end

-- danger level similar to gas rat
-- damage of 1000 is too high
ProjectileRocket.rocket_explode = function(self)
    if Managers.player.is_server and not self.exploded then
        local actor = self.actor
        local position = Actor.position(actor)
        local rotation = Actor.rotation(actor)
        local attacker_unit_id = self.attacker_goid
        local explosion_template_name = "doomrocket_explosion"
        local explosion_template_id = NetworkLookup.explosion_templates[explosion_template_name]
        local explosion_template = ExplosionTemplates[explosion_template_name]
        local damage_source = "skaven_doomrocket"
        local damage_source_id = NetworkLookup.damage_sources[damage_source]
        local is_husk = true
        -- local power_level = 1000
        local power_level = 700
        local world = self.world


		Managers.state.network.network_transmit:send_rpc_clients("rpc_create_explosion", attacker_unit_id, false,
            position, rotation, explosion_template_id, 1, damage_source_id, power_level, false, attacker_unit_id)
        Managers.state.network.network_transmit:send_rpc_server("rpc_create_explosion", attacker_unit_id, false,
            position, rotation, explosion_template_id, 1, damage_source_id, power_level, false, attacker_unit_id)

        Managers.state.unit_spawner:mark_for_deletion(self.unit)

        self.exploded = true
	end

    -- Unit.set_unit_visibility(self.unit, false)
    -- Unit.disable_physics(self.unit)
end

ProjectileRocket.destroy = function(self)

    if self.exhaust_sound_id then
        WwiseWorld.set_source_parameter(self.wwise_world, self.wwise_source_id, "ratling_gun_shooting_loop_parameter", 100)
        WwiseWorld.trigger_event(self.wwise_world, "player_enemy_warpfire_thrower_shoot_end", self.unit)
        WwiseWorld.stop_event(self.wwise_world, self.exhaust_sound_id)
        self.exhaust_sound_id = nil
        self.wwise_source_id = nil
    end

    if self.exhaust_id then
        World.destroy_particles(self.world, self.exhaust_id)
        self.exhaust_id = nil
    end

    if self.unit then
        mod.projectiles[self.unit] = nil
        Unit.destroy_actor(self.unit, 'pRocket')
    end
    self.unit = nil
    self.actor = nil
    self.unit_string = nil
    self.exploded = nil
end
