local mod = get_mod("doomrocket")
Pickups = Pickups or {}

Pickups.level_events.doom_rocket = {
    additional_data_func = "doom_rocket",
	debug_pickup_category = "level_event",
	hud_description = "doom_rocket",
	individual_pickup = false,
	item_description = "doom_rocket",
	item_name = "doom_rocket",
	only_once = true,
	slot_name = "slot_level_event",
	spawn_weighting = 1,
	type = "doom_rocket",
	unit_name = "units/weapons/player/pup_explosive_barrel/pup_explosive_barrel_01",
	unit_template_name = "explosive_pickup_projectile_unit",
	wield_on_pickup = false,
}

mod:dofile('scripts/settings/equipment/pickups')

function create_lookup(lookup, hashtable)
	local i = #lookup

	for key, _ in pairs(hashtable) do
		i = i + 1
		lookup[i] = key
	end

	return lookup
end

-- NetworkLookup.pickup_names = create_lookup({}, AllPickups)

local num_pickups = #NetworkLookup.pickup_names + 1
NetworkLookup.pickup_names[num_pickups] = "doom_rocket"
NetworkLookup.pickup_names["doom_rocket"] = num_pickups

ItemMasterList = ItemMasterList or {}
ItemMasterList.doom_rocket = {
	gamepad_hud_icon = "consumables_icon_defence",
	hud_icon = "consumables_icon_defence",
	inventory_icon = "icons_placeholder",
	is_local = true,
	item_type = "explosive_inventory_item",
	left_hand_unit = "units/weapons/player/wpn_explosive_barrel/wpn_explosive_barrel_01",
	rarity = "plentiful",
	slot_type = "healthkit",
	temporary_template = "explosive_barrel",
	can_wield = CanWieldAllItemTemplates,
}

local num_items = #NetworkLookup.item_names + 1
NetworkLookup.item_names[num_items] = "doom_rocket"
NetworkLookup.item_names["doom_rocket"] = num_items
