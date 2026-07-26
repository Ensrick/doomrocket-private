-- Doomrocket's additions to the vanilla unit extension template table.
--
-- This replaces the old approach of hooking _G.require to swap in a full 2024 copy of
-- scripts/network/unit_extension_templates. That copy reverted the entire game's
-- extension table for every player: by 6.11.3 it was missing AIGroupMember on 23 AI
-- templates, ObjectiveUnitExtension on 10 more, the husk BuffAreaExtension, and the
-- objective_group / objective_pickup_unit / ai_skin_unit / explosive_barrel_socket
-- templates outright, while re-adding a HealthTriggerExtension vanilla had removed.
--
-- Merging two entries into the live table instead keeps every vanilla template current
-- and immune to future patches.

local additions = {
	ai_unit_doomrocket = {
		base_template = "ai_unit_base",
		go_type = "ai_unit_doomrocket",
		self_owned_extensions = {
			"AIInventoryExtension",
			"GenericUnitAimExtension",
			"PingTargetExtension",
		},
		husk_extensions = {
			"AIInventoryExtension",
			"GenericUnitAimExtension",
			"PingTargetExtension",
		},
	},
	doomrocket_projectile = {
		go_type = "doomrocket_projectile",
		self_owned_extensions = {
			"GenericHealthExtension",
			"GenericHitReactionExtension",
			"GenericDeathExtension",
			"ObjectiveLightOutlineExtension",
		},
		husk_extensions = {
			"GenericHealthExtension",
			"GenericHitReactionExtension",
			"GenericDeathExtension",
			"ObjectiveLightOutlineExtension",
		},
	},
}

local extension_table_names = {
	"self_owned_extensions",
	"self_owned_extensions_server",
	"husk_extensions",
	"husk_extensions_server",
}

-- Mirrors the normalization pass at the tail of scripts/network/unit_extension_templates.lua
-- (base_template inheritance, NAME, and the precomputed num_* counts get_extensions reads).
-- Entries merged in after that pass has already run would otherwise be missing all of it.
local function normalize(unit_templates, template_name)
	local template_data = unit_templates[template_name]

	template_data.NAME = template_name

	for i = 1, #extension_table_names do
		local extension_table_name = extension_table_names[i]
		local extension_list = template_data[extension_table_name] or {}
		local extension_list_n = #extension_list
		local base_template_name = template_data.base_template

		if base_template_name ~= nil then
			local inherited = unit_templates[base_template_name]
			local inherited_list = inherited and inherited[extension_table_name]

			if inherited_list then
				for j = 1, #inherited_list do
					extension_list_n = extension_list_n + 1
					extension_list[extension_list_n] = inherited_list[j]
				end
			end

			local inherited_rwk = inherited and inherited.remove_when_killed and inherited.remove_when_killed[extension_table_name]

			if inherited_rwk then
				template_data.remove_when_killed = template_data.remove_when_killed or {}
				template_data.remove_when_killed[extension_table_name] = template_data.remove_when_killed[extension_table_name] or {}

				local remove_when_killed = template_data.remove_when_killed[extension_table_name]

				for j = 1, #inherited_rwk do
					remove_when_killed[#remove_when_killed + 1] = inherited_rwk[j]
				end
			end
		end

		template_data[extension_table_name] = extension_list
		template_data["num_" .. extension_table_name] = extension_list_n
	end

	local remove_when_killed = template_data.remove_when_killed

	if remove_when_killed then
		for i = 1, #extension_table_names do
			local extension_table_name = extension_table_names[i]
			local extension_list = remove_when_killed[extension_table_name]

			if extension_list then
				remove_when_killed["num_" .. extension_table_name] = #extension_list
			end
		end
	end
end

-- Idempotent: safe whether or not require caches, and safe to call on every require.
return function (unit_templates)
	for template_name, template_data in pairs(additions) do
		if not unit_templates[template_name] then
			unit_templates[template_name] = table.clone(template_data)

			normalize(unit_templates, template_name)
		end
	end

	return unit_templates
end
