import pymel.core as pm

'''this class has adds controls to a wrap deformer.
the user supplies the hi-res and lo-res mesh.
a cluster is created for each vert in the lo-res mesh.
a polySphere is placed at the same location and the cluster is constrained to it.
the user can now select groups of spheres to place in a line.
the line or sphere can be manipulated without changing selection mask.
the user would then align the lo-res mesh to the hi-res mesh and shrink wrap it
see: http://chrisrogers3d.com/#portfolioModal2
chris rogers 2016
'''

class FaceCurves(object):
   def __init__(self):
       self.lomesh = None
       self.midmesh = None
       self.himesh = None

   def make_mid_mesh(self):
       pass

   def make_balls(self, mesh=None):
       '''this creates a cluster on each vertex and constrains that to a sphere in the same place
       '''
       if mesh is None:
           mesh = pm.ls(sl=True)[0]
       if mesh is None:
           print "select a mesh."
           return
       nv = pm.polyEvaluate(v=True)
       for vertn in range(nv):
           p = pm.pointPosition(mesh+'.vtx['+str(vertn)+']', w=True)
           ps = pm.polySphere(r=0.2, sx=6, sy=6, name='ps_'+str(vertn))
           pm.xform(ps, t=p, a=True, ws=True)
           pm.select(mesh+'.vtx['+str(vertn)+']')
           cl = pm.cluster(name='cl_'+str(vertn) )
           pm.pointConstraint(ps, cl)

   def make_curve(self):
       '''this will make a curve from the selected balls
       '''
       balls = pm.ls(sl=True)
       pts =[]
       for b in balls:
           p = pm.xform(b,q=True,t=True,ws=True)
           pts.append(p)
       crv = pm.curve(degree=1,p=pts )
       pm.xform(crv, cp=True)

       clusters=[]
       for i in range(len(pts)):
           pm.select(crv+'.cv['+str(i)+']')
           cl = pm.cluster(name='crvcl_'+str(i) , relative=True, envelope=1)
           clusters.append(cl)
           pm.parent(cl,crv)

       for n in range(len(balls)):
           pm.parent(balls[n], crv)
           pc= pm.pointConstraint(balls[n],clusters[n])
           p = pm.xform(balls[n],q=True, t=True, ws=True)
           pm.xform(pc,t=p, ws=True)


