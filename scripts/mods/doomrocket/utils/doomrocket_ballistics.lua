local mod = get_mod("doomrocket")

local DoomrocketBallistics = {
	GRAVITY = 9.82,
	SECONDS_PER_METRE = 0.13,
	-- Keep close shots beyond ProjectileRocket's 0.35 s muzzle-clear/impact-arm
	-- delay, but do not force every target inside 13 m through the same tall lob.
	MIN_FLIGHT_TIME = 0.4,
	MAX_FLIGHT_TIME = 3.4,
	MUZZLE_BACKSTEP = 0.25,
	MIN_LAUNCH_SPEED_SQUARED = 0.01,
}

-- Return the initial velocity that reaches target_position after a deterministic,
-- range-clamped flight time under Stingray's -Z gravity. Keeping this calculation
-- here gives the animation pose and the spawned projectile one source of truth.
DoomrocketBallistics.solve_launch_velocity = function (start_position, target_position)
	if not Vector3.is_valid(start_position) or not Vector3.is_valid(target_position) then
		return nil, nil
	end

	local displacement = target_position - start_position
	local flat_distance = Vector3.length(Vector3.flat(displacement))
	local flight_time = math.clamp(
		flat_distance * DoomrocketBallistics.SECONDS_PER_METRE,
		DoomrocketBallistics.MIN_FLIGHT_TIME,
		DoomrocketBallistics.MAX_FLIGHT_TIME
	)
	local launch_velocity = Vector3(
		displacement.x / flight_time,
		displacement.y / flight_time,
		displacement.z / flight_time + 0.5 * DoomrocketBallistics.GRAVITY * flight_time
	)

	-- A zero (or quantizer-sized near-zero) vector is finite, but consumers must
	-- normalize it for both the animation constraint and projectile rotation.
	if not Vector3.is_valid(launch_velocity)
		or Vector3.length_squared(launch_velocity) <= DoomrocketBallistics.MIN_LAUNCH_SPEED_SQUARED then
		return nil, nil
	end

	return launch_velocity, flight_time
end

mod.doomrocket_ballistics = DoomrocketBallistics
