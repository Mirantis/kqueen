Math.radians = function(degrees) {
    return degrees * Math.PI / 180;
};

// Converts from radians to degrees.
Math.degrees = function(radians) {
    return radians * 180 / Math.PI;
};
/**
 * Module with K8SVisualisations hive chart
 */
var K8SVisualisations = function(K8SVisualisations) {
    K8SVisualisations.hiveChart = K8SVisualisations.hiveChart || {};

    K8SVisualisations.hiveChart.init = function(selector, data, config) {
        config = config || {};
        if (!data) {
            throw new Error("Cannot init K8S hive chart visualisation, invalid data given " + data);
        }
        var width = config.width || 960,
            height = config.height || 600,
            outerRadius = config.outerRadius || 400,
            innerRadius = config.innerRadius || 40,
            axes = [{
                    x: 0,
                    angle: 30,
                    radius: 420,
                    name: "Pods",
                    kind: "Pod"
                },
                {
                    x: 1,
                    angle: 270,
                    radius: 200,
                    name: "Nodes",
                    kind: "Node"
                },
                {
                    x: 2,
                    angle: 150,
                    radius: 240,
                    name: "Services",
                    kind: "Service"
                },
                {
                    x: 3,
                    angle: 210,
                    radius: 240,
                    name: "Deployments",
                    kind: "Deployment"
                },
                {
                    x: 4,
                    angle: 90,
                    radius: 240,
                    name: "Namespaces",
                    kind: "Namespace"
                }
            ],
            icon_mapping = {
                Pod: "\uf1b3", // engine
                Node: "\ue621", // server
                Service: "\ue61e", // web
                Deployment: "\ue624", // other services
                Namespace: "\uf247", // other services
                Container: "\ue624" // other services
            },
            font_mapping = {
                Pod: "FontAwesome", // engine
                Node: "PatternFlyIcons-webfont", // server
                Service: "PatternFlyIcons-webfont", // web
                Deployment: "PatternFlyIcons-webfont", // other services
                Namespace: "FontAwesome", // other services
                Container: "PatternFlyIcons-webfont" // other services
            },
            color_mapping = {
                Pod: "#1186C1",
                Node: "#636363",
                Service: "#ff7f0e",
                Deployment: "#9467bd",
                Namespace: "gray",
                Container: "#ff7f0e"
            },
            itemCounters = {
                Pod: 0,
                Node: 0,
                Service: 0,
                Deployment: 0,
                Namespace: 0,
                Container: 0
            },
            axisMapping = {
                Pod: 0,
                Node: 1,
                Service: 2,
                Deployment: 3,
                Namespace: 4,
                Container: 5
            },
            radius_mapping = {
                Pod: d3.scale.linear().range([innerRadius, 420]),
                Node: d3.scale.linear().range([innerRadius, 200]),
                Service: d3.scale.linear().range([innerRadius, 240]),
                Deployment: d3.scale.linear().range([innerRadius, 240]),
                Namespace: d3.scale.linear().range([innerRadius, 240])
            },
            createNodes = function(items) {
                return items.map(function(item) {
                    item["id"] = item.metadata.uid;
                    item["name"] = item.metadata.name || "Unnamed node";
                    if (["Pod", "Service", "Node", "Deployment", "Namespace"].indexOf(item.kind) < 0) {
                        item.kind = "Other";
                    }
                    item["x"] = axisMapping[item.kind];
                    itemCounters[item.kind]++;
                    item["y"] = itemCounters[item.kind];
                    return item;
                });
            },
            createLinks = function(nodes, relations) {
                return relations.map(function(link) {
                    var retLink = {};
                    nodes.forEach(function(node) {
                        if (link.source == node.id) {
                            retLink.source = node;
                        } else if (link.target == node.id) {
                            retLink.target = node;
                        }
                    });
                    if (!retLink.hasOwnProperty("source") || !retLink.hasOwnProperty("target")) {
                        console.log("Cannot found relation node for link " + link);
                        retLink = link;
                    }
                    return retLink;
                });
            };

        if (typeof data.items === 'object') {
            data.items = Object.values(data.items);
        }

        var nodes = createNodes(data.items);

        var itemStep = {
            Service: 1 / itemCounters.Service,
            Pod: 1 / itemCounters.Pod,
            Node: 1 / itemCounters.Node,
            Deployment: 1 / itemCounters.Deployment,
            Namespace: 1 / itemCounters.Namespace
        };

        var links = createLinks(nodes, data.relations);

        var angle = function(d) {
            var angle = 0,
                found = false;
            axes.forEach(function(item) {
                if (d.kind == item.kind) {
                    angle = item.angle;
                    found = true;
                }
            });
            if (!found) {
                console.log("Cannot compute angle for item " + d.kind + d.metadata.name)
            }
            return angle
        }
        var radius = d3.scale.linear().range([innerRadius, outerRadius]);
        var icon = function(i) {
            return icon_mapping[i]
        };
        var color = function(i) {
            return color_mapping[i]
        };

        var mouseFunctions = {
            linkOver: function(d) {
                svg.selectAll(".link").classed("active", function(p) {
                    return p === d;
                });
                svg.selectAll(".node circle").classed("active", function(p) {
                    return p === d.source || p === d.target;
                });
                svg.selectAll(".node text").classed("active", function(p) {
                    return p === d.source || p === d.target;
                });
                //NodeMouseFunctions.over();
            },
            nodeOver: function(d) {
                svg.selectAll(".link").classed("active", function(p) {
                    return p.source === d || p.target === d;
                });
                d3.select(this).select("circle").classed("active", true);
                d3.select(this).select("text").classed("active", true);
                tooltip.html("Node - " + d.name + "<br/>" + "Kind - " + d.kind)
                    .style("left", (d3.event.pageX + 5) + "px")
                    .style("top", (d3.event.pageY - 28) + "px");
                tooltip.transition()
                    .duration(200)
                    .style("opacity", .9);
            },
            out: function(d) {
                svg.selectAll(".active").classed("active", false);
                tooltip.transition()
                    .duration(500)
                    .style("opacity", 0);
            }
        };

        var svg = d3.select(selector)
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", "translate(" + (width / 2 - 180) + "," + (height / 2 - 20) + ")");

        var tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);

        // Hive plot render

        var axe = svg.selectAll(".node").data(axes)
            .enter().append("g");

        axe.append("line")
            .attr("class", "axis")
            .attr("transform", function(d) {
                return "rotate(" + d.angle + ")";
            })
            .attr("x1", function(d) {
                return radius_mapping[d.kind].range()[0]
            })
            .attr("x2", function(d) {
                return radius_mapping[d.kind].range()[1]
            });

        axe.append("text")
            .attr("class", "axis-label")
            .attr('font-size', '16px')
            .attr('font-family', 'Open Sans')
            .attr('text-anchor', 'middle')
            .attr('alignment-baseline', 'central')
            .text(function(d) {
                return d.name;
            })
            .attr("transform", function(d) {
                var x = (radius_mapping[d.kind].range()[1] + 30) * Math.cos(Math.radians(d.angle));
                var y = (radius_mapping[d.kind].range()[1] + 30) * Math.sin(Math.radians(d.angle));
                return "translate(" + x + ", " + y + ")";
            });

        svg.selectAll(".link").data(links)
            .enter().append("path")
            .attr("class", "link")
            .attr("d", d3.hive.link()
                .angle(function(d) {
                    return Math.radians(angle(d));
                })
                .radius(function(d) {
                    return radius_mapping[d.kind](d.y * itemStep[d.kind] - 0.1);
                }))
            //.style("stroke", function(d) { return color(d.source.kind); })
            .on("mouseover", mouseFunctions.linkOver)
            .on("mouseout", mouseFunctions.out);

        var node = svg.selectAll(".node").data(nodes)
            .enter().append("g")
            .attr("class", "node")
            .attr("transform", function(d) {
                var x = radius_mapping[d.kind](d.y * itemStep[d.kind] - 0.1) * Math.cos(Math.radians(angle(d)));
                var y = radius_mapping[d.kind](d.y * itemStep[d.kind] - 0.1) * Math.sin(Math.radians(angle(d)));
                return "translate(" + x + ", " + y + ")";
            })
            .on("mouseover", mouseFunctions.nodeOver)
            .on("mouseout", mouseFunctions.out);

        if(config.hasOwnProperty("nodeClickFn") && typeof config.nodeClickFn === 'function'){
          node.on("click", config.nodeClickFn);
        }

        node.append("circle")
            .attr("r", 15);

        node.append("text")
            .attr('font-family', function(d) {
                return font_mapping[d.kind];
            })
            //          .attr("color", function(d) { return color(d.kind); })
            .style("stroke", function(d) {
                return color(d.kind);
            })
            .style("fill", function(d) {
                return color(d.kind);
            })
            .attr('font-size', function(d) {
                return '18px';
            })
            .text(function(d) {
                return icon(d.kind);
            })
            .attr("x", "-10px")
            .attr("y", "5px");
    };
    return K8SVisualisations;
}(K8SVisualisations || {});