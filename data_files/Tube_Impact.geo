// Gmsh project created on Thu Jun 22 15:28:17 2023
SetFactory("OpenCASCADE");
//+
Circle(1) = {0, 0, 0, 25.4, 0, 2*Pi};
//+
Circle(2) = {250, 0, 60, 25.4, 0, 2*Pi};
//+
Rotate {{0, 1, 0}, {250, 0, 60}, Pi/2} {
  Curve{2}; 
}
//+
Rotate {{0, 1, 0}, {0, 0, 0}, Pi/2} {
  Curve{1}; 
}
//+
Rotate {{0, 0, 1}, {0, 0, 0}, Pi/2} {
  Curve{1}; 
}
//+
Translate {0, 125, 0} {
  Curve{1}; 
}
//+
Translate {-125, 0, 0} {
  Curve{2}; 
}
//+
Extrude {0, -250, 0} {
  Curve{1}; 
}
//+
Extrude {-250, 0, 0} {
  Curve{2}; 
}
//+
MeshSize {6, 5, 4, 3} = 5;

