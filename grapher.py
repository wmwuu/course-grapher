import sys
import json
import networkx as nx
import plotly.graph_objects as go

courses_dict = {}

# read from courses.json
try:
    with open("courses.json", "r") as file:
        courses_dict = json.load(file)
except FileNotFoundError:
    sys.exit("Could not find courses.json")
except json.JSONDecodeError:
    sys.exit("Malformed JSON in courses.json")

courses_graph = nx.DiGraph()

# populate graph
print("Populating graph...")
# add nodes
for dept_abbr in courses_dict:
    dept_dict = courses_dict[dept_abbr]
    for course_code in dept_dict:
        courses_graph.add_node(course_code, size=1)

# add edges
for dept_abbr in courses_dict:
    dept_dict = courses_dict[dept_abbr]
    for course_code, course_dict in dept_dict.items():
        if "prereqs" in course_dict:
            for prereq_code in course_dict["prereqs"]:
                if prereq_code in courses_graph:
                    # edge points from prereq to course
                    courses_graph.add_edge(prereq_code, course_code)
                    # also increment size of the prereq node
                    courses_graph.nodes[prereq_code]["size"] += 1

# calculate node positions
print("Calculating node positions...")
# group nodes by size
tiny_nodes = []
small_nodes = []
medium_nodes = []
large_nodes = []
for node in courses_graph:
    node_size = courses_graph.nodes[node]["size"]
    if node_size <= 1:
        tiny_nodes.append(node)
    elif node_size <= 3:
        small_nodes.append(node)
    elif node_size <= 10:
        medium_nodes.append(node)
    else:
        large_nodes.append(node)

# arrange nodes in shells - could use nx.shell_layout() but we want more
# control over the radii
node_positions = nx.circular_layout(large_nodes, scale=500) # returns a dict
# of (x, y) tuples, keyed by node
node_positions.update(nx.circular_layout(medium_nodes, scale=750))
node_positions.update(nx.circular_layout(small_nodes, scale=1000))
node_positions.update(nx.circular_layout(tiny_nodes, scale=1250))

# draw graph
print("Generating figure...")
# build a single node trace and a list of individual edge traces
node_trace = go.Scattergl(x=[], y=[], hovertext=[], hoverinfo="text",
                        mode="markers", marker=dict(size=[], line=None))
#edge_traces = []
edge_trace = go.Scattergl(x=[], y=[], mode="lines",
                          line=dict(width=1, color="gray"))

i = 0
for node in courses_graph.nodes:
    # add a marker to the node trace
    x0, y0 = node_positions[node]
    size = courses_graph.nodes[node]["size"]
    marker_size = min(max(size * 2, 4), 200)
    node_trace["x"] += (x0,)
    node_trace["y"] += (y0,)
    node_trace["hovertext"] += (node + " (" + str(size - 1) + ")",)
    node_trace["marker"]["size"] += (marker_size,)

    # create edge traces for all outgoing edges from this node
    for successor in courses_graph.successors(node):
        # successors are courses that this course is a prerequisite of

        # can use courses_graph.get_edge_data(node, successor) if edge attrs
        # are needed (such as weight)
        x1, y1 = node_positions[successor]
        #text = node + " leads to " + successor
        #edge_trace = go.Scattergl(x=[x0, x1], y=[y0, y1], text=text,
        #                        hoverinfo="text", mode="lines",
        #                        line=dict(width=1,color="gray"))
        #edge_traces.append(edge_trace)
        edge_trace["x"] += (x0, x1, None) # None creates gap
        edge_trace["y"] += (y0, y1, None)
    if i % 100 == 0:
        print(i)
    i += 1

# set up and display the figure
layout = go.Layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                   xaxis=dict(showgrid=False, zeroline=False),
                   yaxis=dict(showgrid=False, zeroline=False))
figure = go.Figure(layout=layout)

figure.add_trace(node_trace)
#for trace in edge_traces:
#    figure.add_trace(trace)
figure.add_trace(edge_trace)

figure.update_layout(showlegend=False)
figure.update_xaxes(showticklabels=False)
figure.update_yaxes(showticklabels=False)

print("Displaying figure...")
figure.show()
