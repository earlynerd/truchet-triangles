import svgwrite
import random
import math

def draw_arc(dwg, group, center, radius, start_angle, end_angle, **kwargs):
    """
    A helper function that draws two paths: a filled wedge for the background
    and a stroked arc on top for the visible line.
    """
    if radius <= 0:
        return

    # Calculate coordinates and SVG flags
    start_x = center[0] + radius * math.cos(start_angle)
    start_y = center[1] + radius * math.sin(start_angle)
    end_x = center[0] + radius * math.cos(end_angle)
    end_y = center[1] + radius * math.sin(end_angle)

    angle_diff = end_angle - start_angle
    large_arc_flag = '1' if abs(angle_diff) > math.pi else '0'
    sweep_flag = '1'

    # --- Path 1: The Opaque Fill Layer ---
    # A closed wedge shape (center -> start -> arc -> end -> center).
    # This path has a fill but NO stroke.
    d_fill = (
        f"M {center[0]},{center[1]} "
        f"L {start_x},{start_y} "
        f"A {radius},{radius} 0 {large_arc_flag} {sweep_flag} {end_x},{end_y} "
        f"Z"
    )
    fill_path = dwg.path(
        d=d_fill,
        fill=kwargs.get('fill', 'none'),
        stroke='none'  # Explicitly disable the stroke
    )
    group.add(fill_path)

    # --- Path 2: The Visible Stroke Layer ---
    # An open arc shape (start -> arc -> end).
    # This path has a stroke but NO fill.
    d_stroke = (
        f"M {start_x},{start_y} "
        f"A {radius},{radius} 0 {large_arc_flag} {sweep_flag} {end_x},{end_y}"
    )
    stroke_path = dwg.path(
        d=d_stroke,
        fill='none', # Explicitly disable the fill
        stroke=kwargs.get('stroke', 'none'),
        stroke_width=kwargs.get('stroke_width', 1),
        stroke_linecap=kwargs.get('stroke_linecap', 'round')
    )
    group.add(stroke_path)
    
def create_tri_grid(width, border, max_lines):
    """Creates the initial grid of six large equilateral triangles."""
    tri = []
    tri_base = (width - 2.0 * border) / 2
    tri_height = math.sin(math.pi / 3) * tri_base
    start_x = -tri_base
    start_y = 0
    
    # Define points for the hexagonal grid structure
    points = [
        ([start_x, start_y], [start_x + tri_base, start_y], [start_x + tri_base / 2, start_y - tri_height], 0),
        ([start_x + tri_base / 2, start_y - tri_height], [start_x + 3 * tri_base / 2, start_y - tri_height], [start_x + tri_base, start_y], 1),
        ([start_x + tri_base, start_y], [start_x + 2 * tri_base, start_y], [start_x + 3 * tri_base / 2, start_y - tri_height], 0),
        ([start_x, start_y], [start_x + tri_base, start_y], [start_x + tri_base / 2, start_y + tri_height], 1),
        ([start_x + tri_base / 2, start_y + tri_height], [start_x + 3 * tri_base / 2, start_y + tri_height], [start_x + tri_base, start_y], 0),
        ([start_x + tri_base, start_y], [start_x + 2 * tri_base, start_y], [start_x + 3 * tri_base / 2, start_y + tri_height], 1)
    ]
    
    for p1, p2, p3, orientation in points:
        tri.append([p1, p2, p3, orientation, max_lines])
    return tri

def split_triangle(t):
    """Splits a single triangle into four smaller ones."""
    p1, p2, p3, orientation, line_count = t
    m12 = [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2]
    m23 = [(p2[0] + p3[0]) / 2, (p2[1] + p3[1]) / 2]
    m13 = [(p1[0] + p3[0]) / 2, (p1[1] + p3[1]) / 2]
    
    new_line_count = line_count / 2
    
    return [
        [p1, m12, m13, orientation, new_line_count],
        [m12, p2, m23, orientation, new_line_count],
        [m13, m23, p3, orientation, new_line_count],
        [m13, m23, m12, (orientation + 1) % 2, new_line_count]
    ]

def run_triangle_recursion(initial_triangles, min_recurs, max_recurs, split_chance):
    """Recursively subdivides triangles based on the specified rules."""
    current_triangles = initial_triangles
    final_triangles = []

    for i in range(max_recurs):
        next_tri_holder = []
        if i < min_recurs:  # Always split if below minimum recursion depth
            for t in current_triangles:
                next_tri_holder.extend(split_triangle(t))
        else:  # Split based on random chance
            for t in current_triangles:
                if random.randrange(100) < split_chance:
                    next_tri_holder.extend(split_triangle(t))
                else:
                    final_triangles.append(t)
        current_triangles = next_tri_holder
    
    final_triangles.extend(current_triangles) # Add any remaining triangles
    return final_triangles
    

def draw_truchet_pattern(dwg, t, group, line_spacing, weight, line_color, back_color):
    """Draws the randomized Truchet tile pattern inside a single triangle."""
    start_pt = random.randrange(3)
    side_length = math.dist(t[0], t[1])
    line_capacity = t[4]

    n = int(math.floor(math.cos(math.pi / 6) * line_capacity))

    if n * line_spacing + weight / 1.2 >= math.cos(math.pi / 6) * side_length:
        if n > 0:
            n -= 1
    
    m = int(line_capacity - n)

    if m > n:
        m = n

    p1 = random.randrange(m, n + 1) if m <= n else n
    p2 = line_capacity - p1

    for i in range(3):
        center_pt = t[(start_pt + i) % 3]
        orientation = t[3]

        angles = [
            [(5 * math.pi / 3, 2 * math.pi), (math.pi, 4 * math.pi / 3), (math.pi / 3, 2 * math.pi / 3)],
            [(0, math.pi / 3), (2 * math.pi / 3, math.pi), (4 * math.pi / 3, 5 * math.pi / 3)]
        ]
        a1, a2 = angles[orientation][(start_pt + i) % 3]
        
        num_arcs = int(n) if i < 2 else int(min(p1, p2))

        for j in range(num_arcs):
            r = (num_arcs - j) * line_spacing
            # FIX: Add fill=back_color to the arc call.
            draw_arc(dwg, group, center_pt, r, a1, a2, fill=back_color, stroke=line_color, stroke_width=weight, stroke_linecap='round')

        circle = dwg.circle(center=center_pt, r=weight / 2, fill=line_color)
        group.add(circle)
        
def main():
    """Main function to set up and generate the SVG image."""
    # --- Configuration ---
    filename = "truchet_triangles.svg"
    width, height = 2000, 2000
    border = 150
    back_color = 'white'
    line_color = 'black'

    # --- SVG Initialization ---
    dwg = svgwrite.Drawing(filename, profile='tiny', size=(f"{width}px", f"{height}px"))
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill=back_color))

    # --- Generative Parameters ---
    rot_angle = math.pi / 6
    min_recurs = random.randrange(2)
    max_recurs = random.randrange(min_recurs + 2, 7)
    split_chance = random.randrange(10, 80)
    
    min_lines_options = {5: 2, 4: random.randrange(3, 5), 3: random.randrange(3, 6)}
    min_lines = min_lines_options.get(max_recurs, random.randrange(3, 7))

    max_lines = int(pow(2, max_recurs)) * min_lines
    if max_lines == 0:
        print("Error: max_lines is zero. Adjust parameters.")
        return
        
    line_spacing = (width - 2.0 * border) / 2 / max_lines
    stroke_weight = line_spacing / 2

    # --- Create Transformed Group ---
    main_group = dwg.g(transform=f"translate({width/2}, {height/2}) rotate({math.degrees(rot_angle)})")
    dwg.add(main_group)

    # --- Generate and Draw ---
    initial_triangles = create_tri_grid(width, border, max_lines)
    final_triangles = run_triangle_recursion(initial_triangles, min_recurs, max_recurs, split_chance)

    for t in final_triangles:
        # FIX: Pass the 'back_color' variable.
        draw_truchet_pattern(dwg, t, main_group, line_spacing, stroke_weight, line_color, back_color)

    # --- Save File ---
    dwg.save()
    print(f"🎨 Successfully saved SVG image as '{filename}'")
    

if __name__ == "__main__":
    main()
    