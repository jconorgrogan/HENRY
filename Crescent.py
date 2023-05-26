import numpy as np

class Circle:
    def __init__(self, x, y, radius):
        if radius < 0:
            raise ValueError("Radius must be non-negative.")
        self.x = x
        self.y = y
        self.radius = radius

class Crescent:
    def __init__(self, outer_circle, inner_circle):
        if outer_circle.radius < inner_circle.radius:
            raise ValueError("Outer circle must be larger or equal to inner circle.")
        self.outer_circle = outer_circle
        self.inner_circle = inner_circle

def bounding_boxes_overlap(crescent1, crescent2):
    return not (crescent1.outer_circle.x + crescent1.outer_circle.radius < crescent2.outer_circle.x - crescent2.outer_circle.radius or 
                crescent1.outer_circle.y + crescent1.outer_circle.radius < crescent2.outer_circle.y - crescent2.outer_circle.radius or 
                crescent2.outer_circle.x + crescent2.outer_circle.radius < crescent1.outer_circle.x - crescent1.outer_circle.radius or 
                crescent2.outer_circle.y + crescent2.outer_circle.radius < crescent1.outer_circle.y - crescent1.outer_circle.radius)

def is_point_in_crescent(point, crescent):
    distance_to_outer = np.hypot(crescent.outer_circle.x - point[0], crescent.outer_circle.y - point[1])
    distance_to_inner = np.hypot(crescent.inner_circle.x - point[0], crescent.inner_circle.y - point[1])
    return distance_to_outer <= crescent.outer_circle.radius and distance_to_inner >= crescent.inner_circle.radius

def intersect(circle1, circle2):
    d = np.hypot(circle1.x - circle2.x, circle1.y - circle2.y)
    
    if d > circle1.radius + circle2.radius or d < abs(circle1.radius - circle2.radius) or (d == 0 and circle1.radius == circle2.radius):
        return []
    
    a = (circle1.radius**2 - circle2.radius**2 + d**2) / (2 * d)
    under_sqrt = circle1.radius**2 - a**2
    if under_sqrt < 0:
        return []
        
    h = np.sqrt(under_sqrt)
    x2 = circle1.x + a * (circle2.x - circle1.x) / d
    y2 = circle1.y + a * (circle2.y - circle1.y) / d
    x3 = x2 + h * (circle2.y - circle1.y) / d
    y3 = y2 - h * (circle2.x - circle1.x) / d
    x4 = x2 - h * (circle2.y - circle1.y) / d
    y4 = y2 + h * (circle2.x - circle1.x) / d

    return [(x3, y3), (x4, y4)]

def detect_collision(crescent1, crescent2):
    if crescent1.outer_circle.x == crescent2.outer_circle.x and crescent1.outer_circle.y == crescent2.outer_circle.y and crescent1.outer_circle.radius == crescent2.outer_circle.radius and crescent1.inner_circle.x == crescent2.inner_circle.x and crescent1.inner_circle.y == crescent2.inner_circle.y and crescent1.inner_circle.radius == crescent2.inner_circle.radius:
        return True
    elif not bounding_boxes_overlap(crescent1, crescent2):
        return False

    circles = [crescent1.outer_circle, crescent1.inner_circle, crescent2.outer_circle, crescent2.inner_circle]
    for i in range(len(circles)):
        for j in range(i+1, len(circles)):
            for point in intersect(circles[i], circles[j]):
                if is_point_in_crescent(point, crescent1) and is_point_in_crescent(point, crescent2):
                    return True
    return False


# Test Cases
try:
    c1 = Crescent(Circle(0, 0, 5), Circle(0, 0, 2))
    c2 = Crescent(Circle(10, 10, 5), Circle(10, 10, 2))
    print(detect_collision(c1, c2))  # Should print False (Case 1)

except Exception as e:
    print(str(e))
