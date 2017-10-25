/**
 * Module with K8SVisualisations hive chart
 */
var K8SVisualisations = function(K8SVisualisations) {
    K8SVisualisations = K8SVisualisations || {};
    K8SVisualisations.hiveChart = K8SVisualisations.hiveChart || {};

    K8SVisualisations.hiveChart.init = function(selector, data, config) {
        config = config || {};
        if (!data) {
            throw new Error("Cannot init K8S hive chart visualisation, invalid data given " + data);
        }
        var width = config.width || "auto",
            height = config.height || "auto",
            outerRadius = config.outerRadius || 400,
            innerRadius = config.innerRadius || 60,
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
                Pod: '#vertex-Pod',
                ReplicationController: '#vertex-ReplicationController',
                Node: '#vertex-Node',
                Service: '#vertex-Service',
                ReplicaSet: '#vertex-ReplicaSet',
                Container: '#vertex-Container',
                Deployment: '#vertex-Deployment',
                Namespace: '#vertex-Namespace'
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
            var angle = 0;
            axes.forEach(function(item) {
                if (d.kind == item.kind) {
                    angle = item.angle;
                }
            });
            return angle
        }
        var radius = d3.scale.linear().range([innerRadius, outerRadius]);
        var icon = function(i) {
            return icon_mapping[i]
        };
        var color = function(i) {
            return color_mapping[i]
        };

        // Hive plot render
        function render(){
            var container = d3.select(selector),
                targetHeight,
                targetWidth;
            if(width === "auto"){
                targetWidth = container.node().clientWidth;
            }
            if(height === "auto"){
                targetHeight = container.node().clientHeight;
            }
            container.html("");
            var svg = container
                .append("svg")
                .attr("width", targetWidth)
                .attr("height", targetHeight)
                .append("g")
                .attr("transform", "translate(" + (targetWidth / 2 - 80) + "," + (targetHeight / 2 - 20) + ")");
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
            var tooltip = d3.select("#HiveChartTooltip");
            // tooltip is d3 selection
            if(tooltip.empty()){
              tooltip = d3.select("body").append("div")
                    .attr("id", "HiveChartTooltip")
                    .attr("class", "tooltip")
                   .style("opacity", 0);
            }

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

            svg.selectAll(".link").data(links)
                .enter().append("path")
                .attr("class", "link")
                .attr("d", d3.hive.link()
                    .angle(function(d) {
                        return Math.radians(angle(d));
                    })
                    .radius(function(d) {
                        if(d.kind){
                            return radius_mapping[d.kind](d.y * itemStep[d.kind] - 0.1);
                        }
                        return 0;
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

            node.append("use").attr("xlink:href", function(d) { return icon(d.kind); });
        }
        render();
        window.removeEventListener('resize', render);
        window.addEventListener('resize', render);
    };
    return K8SVisualisations;
}(K8SVisualisations || {});