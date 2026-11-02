-- Numeric-only frame/shape adapter. No temporary native vector survives a call.
local Frames = {}
Frames.__index = Frames
local sqrt, abs = math.sqrt, math.abs
local function dot(a,b) return a[1]*b[1]+a[2]*b[2]+a[3]*b[3] end
local function cross(a,b,out)
    out[1],out[2],out[3]=a[2]*b[3]-a[3]*b[2],a[3]*b[1]-a[1]*b[3],a[1]*b[2]-a[2]*b[1]
    return out
end
local function normalize(v)
    local length=sqrt(dot(v,v))
    if length~=length or length<1e-8 or length>1e6 then return false end
    for i=1,3 do v[i]=v[i]/length end
    return true
end
local function new_pose() return {x_axis={1,0,0},y_axis={0,1,0},z_axis={0,0,1},position={0,0,0}} end
local function copy(a,b) for i=1,3 do b[i]=a[i] end end
local function world_direction(pose,local_direction,out)
    for i=1,3 do out[i]=pose.x_axis[i]*local_direction[1]+pose.y_axis[i]*local_direction[2]+pose.z_axis[i]*local_direction[3] end
end
local function local_direction(pose,v)
    return {dot(v,pose.x_axis),dot(v,pose.y_axis),dot(v,pose.z_axis)}
end
-- Minimal rotation with a deterministic antiparallel axis. Caller supplies a
-- radial direction perpendicular to from; no Quaternion.look pole singularity.
local function rotate(v,from,to,radial,out,k,work)
    local cosine=math.max(-1,math.min(1,dot(from,to)))
    if cosine<-.999999 then
        local projection=dot(v,radial)
        for j=1,3 do out[j]=2*projection*radial[j]-v[j] end
    else
        cross(from,to,k)
        cross(k,v,work)
        local vx,vy,vz=work[1],work[2],work[3]
        cross(k,work,out)
        out[1]=v[1]+vx+out[1]/(1+cosine)
        out[2]=v[2]+vy+out[2]/(1+cosine)
        out[3]=v[3]+vz+out[3]/(1+cosine)
    end
end

-- Half-angle of the circular arc of chord/length ratio r: sin(a)/a = r. The hose
-- only uses this below its authored chord (r <= 0.62), where the curve is smooth.
local ARC_STEPS=64
local ARC_HALF_ANGLE={}
for step=0,ARC_STEPS do
    local ratio,low,high=step/ARC_STEPS,0,math.pi
    for _=1,48 do
        local angle=(low+high)/2
        if angle>0 and math.sin(angle)/angle>ratio then low=angle else high=angle end
    end
    ARC_HALF_ANGLE[step]=(low+high)/2
end
-- At or above this fraction of the authored chord the authored curve is exact.
local ARC_BLEND_START=.75

function Frames.new(profile)
    local n=#profile.controls
    local self=setmetatable({n=n,poses={},offsets={},fractions={},radials={},tangents={},coarse_tangents={},
        chord={},current_chord={},radial={},offset={},rotated={},k={},work={},scratch={},
        bow={0,0,0},sag={0,0,0},frame_x={},frame_y={},frame_z={},roll_x={},roll_y={},twist=0},Frames)
    local first,last=profile.controls[1].rest,profile.controls[n].rest
    local chord={last.position[1]-first.position[1],last.position[2]-first.position[2],last.position[3]-first.position[3]}
    self.rest_chord=local_direction(first,chord)
    local total,travelled=0,0
    for i=1,#profile.lengths do total=total+profile.lengths[i] end
    self.length=total
    self.rest_span=sqrt(dot(chord,chord))
    for i=1,n do
        local rest=profile.controls[i].rest
        local fraction=travelled/total
        local offset={}
        for j=1,3 do offset[j]=rest.position[j]-first.position[j]-fraction*chord[j] end
        self.offsets[i]=local_direction(first,offset)
        self.radials[i]=local_direction(first,rest.x_axis)
        self.tangents[i]=local_direction(first,rest.y_axis)
        -- Preserve the authored dense-curve tangent instead of silently
        -- replacing it by the more coarsely sampled simulation tangent.
        local before=profile.controls[math.max(1,i-1)].rest.position
        local after=profile.controls[math.min(n,i+1)].rest.position
        local tangent={after[1]-before[1],after[2]-before[2],after[3]-before[3]}
        normalize(tangent)
        self.coarse_tangents[i]=local_direction(first,tangent)
        self.fractions[i]=fraction
        self.poses[i]=new_pose()
        for j=1,3 do self.bow[j]=self.bow[j]+self.offsets[i][j]/n end
        if i<n then travelled=travelled+profile.lengths[i] end
    end
    -- Record each authored bone against the rotation-minimizing frame of the rest
    -- curve, so the live frame reproduces the rest pose and its authored roll.
    local x,y,z={1,0,0},{0,1,0},{0,0,1}
    local moved,k,work={},{},{}
    for i=1,n do
        local to=(i==1 or i==n) and self.tangents[i] or self.coarse_tangents[i]
        self.frame_x[i],self.frame_y[i],self.frame_z[i]={1,0,0},{0,1,0},{0,0,1}
        if i>1 then
            rotate(x,y,to,x,moved,k,work)
            copy(moved,x); copy(to,y)
            local projection=dot(x,y)
            for j=1,3 do x[j]=x[j]-projection*y[j] end
            normalize(x); normalize(y); cross(x,y,z)
        end
        self.roll_x[i]={dot(self.radials[i],x),dot(self.radials[i],y),dot(self.radials[i],z)}
        self.roll_y[i]={dot(self.tangents[i],x),dot(self.tangents[i],y),dot(self.tangents[i],z)}
    end
    return self
end

function Frames:shape(solver,pack,weapon)
    world_direction(pack,self.rest_chord,self.chord)
    if not normalize(self.chord) then return false end
    for j=1,3 do self.current_chord[j]=weapon.position[j]-pack.position[j] end
    local span=sqrt(dot(self.current_chord,self.current_chord))
    -- A nearly straight hose cannot retain the full rest bend under tension.
    -- Relax its curvature target continuously using available chord slack;
    -- rest shape is unchanged at its authored chord, and no segment rest length
    -- changes. Full extension has a straight, feasible target.
    local rest_slack=self.length*self.length-self.rest_span*self.rest_span
    local curvature_scale=1
    if span>self.rest_span and rest_slack>1e-10 then
        curvature_scale=math.sqrt(math.max(0,(self.length*self.length-span*span)/rest_slack))
    end
    if not normalize(self.current_chord) then copy(self.chord,self.current_chord) end
    copy(pack.x_axis,self.radial)
    local projection=dot(self.radial,self.chord)
    for j=1,3 do self.radial[j]=self.radial[j]-projection*self.chord[j] end
    if not normalize(self.radial) then
        copy(pack.z_axis,self.radial)
        projection=dot(self.radial,self.chord)
        for j=1,3 do self.radial[j]=self.radial[j]-projection*self.chord[j] end
        if not normalize(self.radial) then return false end
    end
    -- In game the ends sit about 0.35 m apart against a 1.45 m bind chord. The
    -- squeezed authored curve is then 0.5 m shorter than the hose and doubles back
    -- on itself, folding the chain (#3). Below the authored chord, lead into a
    -- circular arc of the hose's full length, hanging on the authored bow's side.
    local arc=1-math.min(1,math.max(0,(span/self.rest_span-ARC_BLEND_START)/(1-ARC_BLEND_START)))
    arc=arc*arc*(3-2*arc)
    local half,curve,cos_half=0,0,0
    if arc>0 then
        local position=math.min(span/self.length,1)*ARC_STEPS
        local step=math.min(math.floor(position),ARC_STEPS-1)
        half=ARC_HALF_ANGLE[step]+(ARC_HALF_ANGLE[step+1]-ARC_HALF_ANGLE[step])*(position-step)
        curve=self.length/(2*half)
        cos_half=math.cos(half)
        world_direction(pack,self.bow,self.offset)
        rotate(self.offset,self.chord,self.current_chord,self.radial,self.sag,self.k,self.work)
        if not normalize(self.sag) then copy(self.radial,self.sag) end
        self.sag[3]=self.sag[3]-.5
        projection=dot(self.sag,self.current_chord)
        for j=1,3 do self.sag[j]=self.sag[j]-projection*self.current_chord[j] end
        if not normalize(self.sag) then
            rotate(self.radial,self.chord,self.current_chord,self.radial,self.sag,self.k,self.work)
            if not normalize(self.sag) then return false end
        end
    end
    for i=1,self.n do
        world_direction(pack,self.offsets[i],self.offset)
        rotate(self.offset,self.chord,self.current_chord,self.radial,self.rotated,self.k,self.work)
        local t=self.fractions[i]
        local angle=half*(2*t-1)
        local along,bulge=math.sin(angle)*curve,(math.cos(angle)-cos_half)*curve
        for j=1,3 do
            local authored=pack.position[j]+t*(weapon.position[j]-pack.position[j])+curvature_scale*self.rotated[j]
            local bowed=(pack.position[j]+weapon.position[j])/2+along*self.current_chord[j]+bulge*self.sag[j]
            self.scratch[j]=authored+(bowed-authored)*arc
        end
        if not solver:set_shape_point(i,self.scratch[1],self.scratch[2],self.scratch[3]) then return false end
    end
    return solver:enable_shape()
end

-- Carry the outlet's frame along the live hose with no spin of its own, so
-- neighbouring bones cannot twist against each other and pinch the skinned tube
-- (#3). The difference from the launcher's roll is spread over the whole length.
function Frames:update(solver,pack,weapon,reinitialize)
    if reinitialize then self.twist=0 end
    local n,x,y,z=self.n,self.frame_x,self.frame_y,self.frame_z
    copy(pack.x_axis,x[1]); copy(pack.y_axis,y[1]); copy(pack.z_axis,z[1])
    for i=2,n do
        local to=y[i]
        if i==n then copy(weapon.y_axis,to)
        else
            to[1]=solver.rx[i+1]-solver.rx[i-1]
            to[2]=solver.ry[i+1]-solver.ry[i-1]
            to[3]=solver.rz[i+1]-solver.rz[i-1]
        end
        if not normalize(to) then return false end
        rotate(x[i-1],y[i-1],to,x[i-1],x[i],self.k,self.work)
        local projection=dot(x[i],to)
        for j=1,3 do x[i][j]=x[i][j]-projection*to[j] end
        if not normalize(x[i]) then return false end
        cross(x[i],to,z[i])
    end
    -- Keep the roll difference continuous from frame to frame instead of wrapping
    -- at half a turn, which would spin every bone at once.
    local roll=self.roll_x[n]
    for j=1,3 do self.scratch[j]=x[n][j]*roll[1]+y[n][j]*roll[2]+z[n][j]*roll[3] end
    cross(self.scratch,weapon.x_axis,self.work)
    local difference=math.atan2(dot(self.work,y[n]),dot(self.scratch,weapon.x_axis))-self.twist
    difference=(difference+math.pi)%(2*math.pi)-math.pi
    self.twist=self.twist+difference
    for i=1,n do
        local pose=self.poses[i]
        if i==1 or i==n then
            local endpoint=i==1 and pack or weapon
            copy(endpoint.x_axis,pose.x_axis); copy(endpoint.y_axis,pose.y_axis); copy(endpoint.z_axis,pose.z_axis)
        else
            local angle=self.twist*(i-1)/(n-1)
            local c,s=math.cos(angle),math.sin(angle)
            local rx,ry=self.roll_x[i],self.roll_y[i]
            for j=1,3 do
                local spun_x,spun_z=x[i][j]*c-z[i][j]*s,z[i][j]*c+x[i][j]*s
                pose.x_axis[j]=spun_x*rx[1]+y[i][j]*rx[2]+spun_z*rx[3]
                pose.y_axis[j]=spun_x*ry[1]+y[i][j]*ry[2]+spun_z*ry[3]
            end
            if not normalize(pose.x_axis) or not normalize(pose.y_axis) then return false end
            cross(pose.x_axis,pose.y_axis,pose.z_axis)
            if not normalize(pose.z_axis) then return false end
        end
        pose.position[1],pose.position[2],pose.position[3]=solver.rx[i],solver.ry[i],solver.rz[i]
    end
    return true
end
return Frames
