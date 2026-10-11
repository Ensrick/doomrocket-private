#!/usr/bin/env python3
"""Issue #15: one scaled, linked warpfire flame on the launcher crystal.

The fixed native billboard clouds are scaled through the engine link pose, with
their rising +Z laid along the crystal. A TEST resize restarts the emitter.

Executes the production controller in Lua 5.1 against strict engine lifetime
doubles (the backpack smoke suite's boundary): handle and package ownership,
start/stop/drop/death/world-release ordering. A deleted launcher recycles its
linked emitter's ID, so cleanup must not reclaim that recycled handle. The anchor is checked against the
measured fixture and, when bundleV2 exists, regenerated from the compiled
launcher node. None of this proves how the flame looks in game.
"""

import json
import math
from pathlib import Path
import re
import subprocess
import sys
import unittest

from lupa.lua51 import LuaRuntime


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "scripts/mods/doomrocket/extensions/doomrocket_crystal_flame.lua"
ANCHOR = ROOT / "scripts/mods/doomrocket/utils/doomrocket_crystal_anchor.lua"
FIXTURE = json.loads((ROOT / "tools/fixtures/warlock_crystal_anchor.json").read_text(encoding="utf-8"))
BOOTSTRAP = ROOT / "scripts/mods/doomrocket/doomrocket.lua"
HOOKS = ROOT / "scripts/mods/doomrocket/utils/hooks.lua"
BUNDLE_ROOT = ROOT / "bundleV2"

HARNESS = r"""
events={created=0,linked=0,destroyed=0,queried=0,loads=0,unloads=0,nodes=0}
function printf() end
local function v(x,y,z) return {x=x,y=y,z=z} end
Vector3=setmetatable({length=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end},
 {__call=function(_,x,y,z) return v(x,y,z) end})
Matrix4x4={
 identity=function() return {x=v(1,0,0),y=v(0,1,0),z=v(0,0,1),p=v(0,0,0)} end,
 set_x=function(m,x) m.x=x end,set_y=function(m,x) m.y=x end,
 set_z=function(m,x) m.z=x end,set_translation=function(m,x) m.p=x end,
 translation=function(m) return m.p end,
 rotation=function(m) return m end,
}
local function transform(m,a,point)
 return v(m.x.x*a.x+m.y.x*a.y+m.z.x*a.z+(point and m.p.x or 0),
  m.x.y*a.x+m.y.y*a.y+m.z.y*a.z+(point and m.p.y or 0),
  m.x.z*a.x+m.y.z*a.y+m.z.z*a.z+(point and m.p.z or 0))
end
-- Stingray composition is local then parent world, as used by native action_sweep.
function Matrix4x4.multiply(local_pose,parent)
 return {x=transform(parent,local_pose.x),y=transform(parent,local_pose.y),
  z=transform(parent,local_pose.z),p=transform(parent,local_pose.p,true)}
end
function Matrix4x4.set_scale(m,scale)
 local function axis(a,s)
  local n=Vector3.length(a)
  return v(a.x/n*s,a.y/n*s,a.z/n*s)
 end
 m.x=axis(m.x,scale.x); m.y=axis(m.y,scale.y); m.z=axis(m.z,scale.z)
end
function Matrix4x4.scale(m)
 return v(Vector3.length(m.x),Vector3.length(m.y),Vector3.length(m.z))
end
world={alive=true}
weapon_name='units/rocket/pRocketLauncher'
function new_owner() return {alive=true,world=world} end
function new_weapon() return {alive=true,world=world,name=weapon_name,has_node=true,item={dropped=false}} end
owner=new_owner(); weapon=new_weapon()
function new_inventory(o,w) return {unit=o or owner,inventory_item_units={{alive=true,world=world,name='units/bombadier/Backpack'},w or weapon}} end
inventory=new_inventory()
Unit={
 alive=function(u) return u and u.alive end,
 world=function(u) assert(u and u.alive,'dead Unit.world'); return u.world end,
 get_data=function(u,key) assert(u and u.alive and key=='unit_name'); return u.name end,
 has_node=function(u,node) assert(u.alive and node=='pRocketLauncher'); return u.has_node end,
 node=function(u,node)
  assert(u.alive and u.has_node and node=='pRocketLauncher','unsafe node lookup')
  events.nodes=events.nodes+1; return 7
 end,
 world_pose=function(u,node)
  assert(u.alive and node==7,'dead or wrong Unit.world_pose')
  return u.pose or {x=v(100,0,0),y=v(0,100,0),z=v(0,0,100),p=v(10,20,30)}
 end,
}
ScriptUnit={has_extension=function(u,system)
 assert(system=='ai_inventory_item_system'); return u.item
end}
wm={_worlds={level_world=world},_disabled_worlds={}}
function wm:has_world(name) return self._worlds[name] ~= nil end
function wm:world(name) assert(self._worlds[name]); return self._worlds[name] end
package_name='resource_packages/breeds/skaven_warpfire_thrower'
package_reference='doomrocket_crystal_flame'
effect_name='fx/chr_warp_fire_flamethrower_remains_01'
package_available=true; particles_available=true; loaded=true
refs={global=3}
pm={}
function pm:has_loaded(name,reference)
 assert(name==package_name)
 return loaded and (not reference or refs[reference] ~= nil)
end
function pm:load(name,reference,callback,asynchronous)
 assert(name==package_name and reference==package_reference)
 assert(callback==nil and asynchronous==nil,'must load synchronously')
 refs[reference]=(refs[reference] or 0)+1; loaded=true; events.loads=events.loads+1
end
function pm:unload(name,reference)
 assert(name==package_name and reference==package_reference)
 assert(refs[reference] and refs[reference] > 0,'unowned package decrement')
 refs[reference]=refs[reference]-1
 if refs[reference]==0 then refs[reference]=nil end
 events.unloads=events.unloads+1
end
Managers={world=wm,package=pm}
Application={can_get=function(kind,name)
 if kind=='package' then assert(name==package_name); return package_available end
 assert(kind=='particles' and name==effect_name)
 assert(refs[package_reference],'residency queried before own package load')
 return particles_available
end}
effects={}; next_id=1
local function check_world(w) assert(w and w.alive,'released world touched') end
World={
 create_particles=function(w,name,position,rotation,scale)
  check_world(w); assert(name==effect_name)
  assert(position and not rotation and not scale,'use the native scaled link-pose pattern')
  local id=next_id; next_id=id+1
  effects[id]={world=w}; events.created=events.created+1
  events.latest_id=id
  return id
 end,
 link_particles=function(w,id,u,node,pose,policy)
  check_world(w); assert(effects[id] and u.alive and u.world==w)
  assert(node==7 and policy=='destroy')
  effects[id].weapon=u; effects[id].node=node; effects[id].pose=pose
  events.linked=events.linked+1; events.last_pose=pose
 end,
 are_particles_playing=function(w,id)
  check_world(w); events.queried=events.queried+1
  assert(effects[id] and effects[id].world==w,'stale particle queried')
  return true
 end,
 destroy_particles=function(w,id)
  check_world(w); assert(effects[id] and effects[id].world==w,'stale particle destroyed')
  assert(not effects[id].foreign,'recycled foreign particle destroyed')
  effects[id]=nil; events.destroyed=events.destroyed+1
 end,
 find_particles_variable=function(w,name,variable)
  error('a ground-fire variable does not size every cloud')
 end,
 set_particles_variable=function(w,id,variable,value)
  error('a ground-fire variable does not size every cloud')
 end,
}
mod={commands={},echoes={}}
function mod:command(name,description,fn) self.commands[name]=fn end
function mod:echo(message,...) self.echoes[#self.echoes+1]=string.format(message,...) end
function get_mod(name) assert(name=='doomrocket'); return mod end
function delete_weapon(w)
 w=w or weapon
 -- Native linking destroys the emitter with the launcher and may recycle its ID.
 for id,e in pairs(effects) do
  if e.weapon==w then effects[id]={world=e.world,foreign=true} end
 end
 w.alive=false
end
function particles_pose(id)
 local e=effects[id]
 assert(e and not e.foreign)
 return Matrix4x4.multiply(e.pose,Unit.world_pose(e.weapon,e.node))
end
function count() local n=0; for _ in pairs(effects) do n=n+1 end; return n end
function start(o,inv) return mod._start_warlock_crystal_flame(o or owner,inv or inventory) end
"""


def runtime():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(HARNESS)
    lua.execute("mod._doomrocket_crystal_anchor = (function()\n"
                + ANCHOR.read_text(encoding="utf-8") + "\nend)()")
    lua.execute(MODULE.read_text(encoding="utf-8"))
    return lua


class CrystalFlameLifecycleTests(unittest.TestCase):
    def test_start_links_one_scaled_flame_at_the_anchor_and_is_idempotent(self):
        lua = runtime()
        lua.execute("""
            assert(start()); assert(start())
            assert(events.created==1 and events.linked==1 and events.loads==1)
            local a, p = mod._doomrocket_crystal_anchor, events.last_pose
            -- Effect +Z rises along the crystal's mount-to-tip axis (anchor +X).
            local function close(a,b) return math.abs(a-b)<1e-12 end
            assert(close(p.z.x,a.x_axis[1]*(0.2/1.2)) and close(p.z.y,a.x_axis[2]*(0.2/1.2)))
            assert(close(p.x.x,a.y_axis[1]*(0.06/0.6)) and close(p.y.x,a.z_axis[1]*(0.06/0.6)))
            assert(p.p.x==a.position[1] and p.p.y==a.position[2] and p.p.z==a.position[3])
            local global=particles_pose(1)
            local scale=Matrix4x4.scale(global)
            assert(close(scale.x,0.06/0.6) and close(scale.y,0.06/0.6) and close(scale.z,0.2/1.2))
            assert(global.p.x==10+a.position[1]*100 and global.p.y==20+a.position[2]*100 and global.p.z==30+a.position[3]*100)
        """)

    def test_stop_destroys_its_own_flame_and_releases_the_package_on_reset(self):
        lua = runtime()
        lua.execute("""
            assert(start())
            assert(mod._stop_warlock_crystal_flame(owner,'test'))
            assert(not mod._stop_warlock_crystal_flame(owner,'again'))
            assert(events.destroyed==1 and count()==0)
            mod._reset_warlock_crystal_flame('test')
            assert(events.unloads==1 and refs[package_reference]==nil and refs.global==3)
        """)

    def test_dropping_or_disabling_the_launcher_stops_only_that_flame(self):
        lua = runtime()
        lua.execute("""
            assert(start())
            assert(not mod._stop_warlock_crystal_flame_item(owner,{alive=true},'other_item'))
            assert(count()==1)
            assert(mod._stop_warlock_crystal_flame_item(owner,weapon,'inventory_drop'))
            assert(events.destroyed==1 and count()==0)
        """)

    def test_deleted_launcher_is_forgotten_without_touching_a_recycled_id(self):
        lua = runtime()
        lua.execute("""
            assert(start())
            delete_weapon()
            mod._update_warlock_crystal_flame()
            assert(events.destroyed==0 and events.queried==0)
            assert(not mod._stop_warlock_crystal_flame(owner,'late'))
        """)

    def test_world_release_forgets_without_particle_calls(self):
        lua = runtime()
        lua.execute("""
            assert(start())
            mod._release_warlock_crystal_flame_world(world)
            assert(events.destroyed==0 and events.queried==0)
            assert(not start(), 'no new flame while the old world is releasing')
            world.alive=false; wm._worlds.level_world=nil
            world={alive=true}; wm._worlds.level_world=world
            owner=new_owner(); weapon=new_weapon(); inventory=new_inventory(owner,weapon)
            assert(start())
        """)

    def test_no_flame_without_a_carried_launcher_or_on_dedicated_servers(self):
        lua = runtime()
        lua.execute("""
            weapon.item.dropped=true
            assert(not start())
            weapon.item.dropped=false
            assert(not start(owner,{unit=new_owner(),inventory_item_units={weapon}}))
            weapon.has_node=false
            assert(not start())
            weapon.has_node=true
            particles_available=false
            assert(not start())
            particles_available=true
            DEDICATED_SERVER=true
            assert(not start())
            DEDICATED_SERVER=nil
            assert(start() and events.created==1)
        """)

    def test_replaced_launcher_moves_the_flame(self):
        lua = runtime()
        lua.execute("""
            assert(start())
            local replacement=new_weapon()
            assert(start(owner,new_inventory(owner,replacement)))
            assert(events.created==2 and events.destroyed==1 and count()==1)
        """)

    def test_native_link_follows_rotated_translated_scale100_launcher_without_respawning(self):
        lua = runtime()
        lua.execute("""
            assert(start())
            weapon.pose={x=Vector3(0,100,0),y=Vector3(-100,0,0),z=Vector3(0,0,100),p=Vector3(50,60,70)}
            mod._update_warlock_crystal_flame()
            local pose,a=particles_pose(events.latest_id),mod._doomrocket_crystal_anchor
            assert(events.created==1 and events.linked==1, 'pose changes never respawn or relink')
            assert(pose.p.x==50-a.position[2]*100 and pose.p.y==60+a.position[1]*100)
            assert(math.abs(pose.z.x+a.x_axis[2]*100*(0.2/1.2))<1e-12)
            assert(math.abs(pose.z.y-a.x_axis[1]*100*(0.2/1.2))<1e-12)
            local scale=Matrix4x4.scale(pose)
            assert(math.abs(scale.x-0.06/0.6)<1e-12 and math.abs(scale.z-0.2/1.2)<1e-12)
            mod._release_warlock_crystal_flame_world(world)
            world.alive=false; wm._worlds.level_world=nil
            mod._update_warlock_crystal_flame()
            assert(events.queried==0, 'released worlds must not be accessed')
        """)


class CrystalFlameTuningTests(unittest.TestCase):
    def test_resize_command_updates_live_flames_and_later_ones(self):
        lua = runtime()
        lua.execute("""
            assert(start())
            mod.commands.warlock_crystal_flame('0.1', '0.35')
            local scale=Matrix4x4.scale(particles_pose(events.latest_id))
            assert(math.abs(scale.x-0.1/0.6)<1e-12 and math.abs(scale.z-0.35/1.2)<1e-12)
            assert(events.created==2 and events.destroyed==1 and count()==1)
            assert(mod.echoes[#mod.echoes]:find('radius 0.100', 1, true))
            mod._stop_warlock_crystal_flame(owner,'test')
            owner=new_owner(); weapon=new_weapon(); inventory=new_inventory(owner,weapon)
            assert(start())
            local latest=Matrix4x4.scale(particles_pose(events.latest_id))
            assert(math.abs(latest.x-0.1/0.6)<1e-12 and math.abs(latest.z-0.35/1.2)<1e-12)
        """)

    def test_bad_or_extreme_sizes_are_rejected_or_clamped(self):
        lua = runtime()
        lua.execute("""
            assert(start())
            mod.commands.warlock_crystal_flame('big')
            assert(events.created==1, 'non-numbers leave the size alone')
            assert(mod.echoes[#mod.echoes]:find('Usage', 1, true))
            mod.commands.warlock_crystal_flame('-1', '50')
            local scale=Matrix4x4.scale(particles_pose(events.latest_id))
            assert(math.abs(scale.x-0.01/0.6)<1e-12 and math.abs(scale.z-2/1.2)<1e-12)
            local before=events.created
            assert(not mod._set_warlock_crystal_flame_size(math.huge,0.2))
            assert(not mod._set_warlock_crystal_flame_size(0.1,-math.huge))
            assert(events.created==before)
        """)

    def test_resize_skips_flames_in_a_releasing_world(self):
        lua = runtime()
        lua.execute("""
            assert(start())
            mod._release_warlock_crystal_flame_world(world)
            local before = events.created
            assert(mod._set_warlock_crystal_flame_size(0.2, 0.2))
            assert(events.created==before)
        """)

    def test_failed_resize_creation_does_not_retain_the_destroyed_handle(self):
        lua = runtime()
        lua.execute("""
            assert(start())
            World.create_particles=function() return nil end
            local valid,live=mod._set_warlock_crystal_flame_size(0.1,0.3)
            assert(valid and live==0 and events.destroyed==1 and count()==0)
            assert(not mod._stop_warlock_crystal_flame(owner,'later'))
            local before=events.queried
            mod._update_warlock_crystal_flame()
            assert(events.queried==before, 'the destroyed handle must not be queried')
        """)


class CrystalFlameWiringTests(unittest.TestCase):
    def test_bootstrap_loads_anchor_then_controller_and_drives_update_and_reset(self):
        source = BOOTSTRAP.read_text(encoding="utf-8")
        anchor = source.index('mod._doomrocket_crystal_anchor = mod:dofile("scripts/mods/doomrocket/utils/doomrocket_crystal_anchor")')
        controller = source.index('mod:dofile("scripts/mods/doomrocket/extensions/doomrocket_crystal_flame")')
        self.assertLess(anchor, controller)
        self.assertIn("mod._update_warlock_crystal_flame()", source)
        self.assertIn('mod._reset_warlock_crystal_flame(reason or "runtime_reset")', source)

    def test_every_smoke_lifecycle_boundary_also_ends_the_flame(self):
        hooks = HOOKS.read_text(encoding="utf-8")
        for call in (
            "mod._start_warlock_crystal_flame(unit, self)",
            'mod._stop_warlock_crystal_flame(self.unit, "inventory_destroy")',
            'mod._stop_warlock_crystal_flame(self.unit, "inventory_freeze")',
            'mod._stop_warlock_crystal_flame_item(self.unit, item_unit, "inventory_drop")',
            'mod._stop_warlock_crystal_flame_item(self.unit, item_unit, "inventory_disable_item")',
            "mod._release_warlock_crystal_flame_world(world)",
            'mod._stop_warlock_crystal_flame(owner_unit, "death_" .. tostring(source))',
        ):
            with self.subTest(call=call):
                self.assertEqual(hooks.count(call), 1)


class CrystalAnchorTests(unittest.TestCase):
    def anchor(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        table = lua.execute(ANCHOR.read_text(encoding="utf-8"))
        return {key: list(table[key].values()) if key != "node" else table[key]
                for key in ("node", "x_axis", "y_axis", "z_axis", "position")}

    def test_anchor_is_the_measured_tip_frame_in_node_units(self):
        # The compiled node is a scale-100 frame at the root with a rotation of
        # about 1.6e-5 rad, so the node-local frame is 0.01 x the root frame.
        anchor = self.anchor()
        self.assertEqual(anchor["node"], FIXTURE["target_node"])
        for key, source in (("x_axis", "frame_x_axis"), ("y_axis", "frame_y_axis"),
                            ("z_axis", "frame_z_axis"), ("position", "tip_engine_m")):
            for actual, expected in zip(anchor[key], FIXTURE[source]):
                self.assertAlmostEqual(actual, expected * 0.01, delta=2e-8, msg=key)
        x, y, z = anchor["x_axis"], anchor["y_axis"], anchor["z_axis"]
        cross = (x[1] * y[2] - x[2] * y[1], x[2] * y[0] - x[0] * y[2], x[0] * y[1] - x[1] * y[0])
        self.assertGreater(sum(c * w for c, w in zip(cross, z)), 0, "anchor frame must stay right-handed")
        self.assertAlmostEqual(math.sqrt(sum(c * c for c in x)), 0.01, delta=1e-9)

    @unittest.skipUnless(BUNDLE_ROOT.is_dir() and any(BUNDLE_ROOT.glob("*.mod_bundle")), "compiled bundleV2 is not present")
    def test_anchor_regenerates_from_the_compiled_launcher_node(self):
        result = subprocess.run([sys.executable, str(ROOT / "tools/build_crystal_anchor.py"), "--check"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
