"use strict";

d3.hive = {};

d3.hive.link = function () {
  var source = function source(d) {
    return d.source;
  },
      target = function target(d) {
    return d.target;
  },
      angle = function angle(d) {
    return d.angle;
  },
      startRadius = function startRadius(d) {
    return d.radius;
  },
      endRadius = startRadius,
      arcOffset = 0;

  function link(d, i) {
    var s = node(source, this, d, i),
        t = node(target, this, d, i),
        x;
    if (t.a < s.a) x = t, t = s, s = x;
    if (t.a - s.a > Math.PI) s.a += 2 * Math.PI;
    var a1 = s.a + (t.a - s.a) / 3,
        a2 = t.a - (t.a - s.a) / 3;
    return s.r0 - s.r1 || t.r0 - t.r1 ? "M" + Math.cos(s.a) * s.r0 + "," + Math.sin(s.a) * s.r0 + "L" + Math.cos(s.a) * s.r1 + "," + Math.sin(s.a) * s.r1 + "C" + Math.cos(a1) * s.r1 + "," + Math.sin(a1) * s.r1 + " " + Math.cos(a2) * t.r1 + "," + Math.sin(a2) * t.r1 + " " + Math.cos(t.a) * t.r1 + "," + Math.sin(t.a) * t.r1 + "L" + Math.cos(t.a) * t.r0 + "," + Math.sin(t.a) * t.r0 + "C" + Math.cos(a2) * t.r0 + "," + Math.sin(a2) * t.r0 + " " + Math.cos(a1) * s.r0 + "," + Math.sin(a1) * s.r0 + " " + Math.cos(s.a) * s.r0 + "," + Math.sin(s.a) * s.r0 : "M" + Math.cos(s.a) * s.r0 + "," + Math.sin(s.a) * s.r0 + "C" + Math.cos(a1) * s.r1 + "," + Math.sin(a1) * s.r1 + " " + Math.cos(a2) * t.r1 + "," + Math.sin(a2) * t.r1 + " " + Math.cos(t.a) * t.r1 + "," + Math.sin(t.a) * t.r1;
  }

  function node(method, thiz, d, i) {
    var node = method.call(thiz, d, i),
        a = +(typeof angle === "function" ? angle.call(thiz, node, i) : angle) + arcOffset,
        r0 = +(typeof startRadius === "function" ? startRadius.call(thiz, node, i) : startRadius),
        r1 = startRadius === endRadius ? r0 : +(typeof endRadius === "function" ? endRadius.call(thiz, node, i) : endRadius);
    return { r0: r0, r1: r1, a: a };
  }

  link.source = function (_) {
    if (!arguments.length) return source;
    source = _;
    return link;
  };

  link.target = function (_) {
    if (!arguments.length) return target;
    target = _;
    return link;
  };

  link.angle = function (_) {
    if (!arguments.length) return angle;
    angle = _;
    return link;
  };

  link.radius = function (_) {
    if (!arguments.length) return startRadius;
    startRadius = endRadius = _;
    return link;
  };

  link.startRadius = function (_) {
    if (!arguments.length) return startRadius;
    startRadius = _;
    return link;
  };

  link.endRadius = function (_) {
    if (!arguments.length) return endRadius;
    endRadius = _;
    return link;
  };

  return link;
};
'use strict';

/**
 * Module with K8SVisualisations forced chart
 */
var K8SVisualisations = function (K8SVisualisations) {
    K8SVisualisations.forcedChart = K8SVisualisations.forcedChart || {};
    K8SVisualisations.forcedChart.cache = {};
    K8SVisualisations.forcedChart.init = function (selector, data, config) {
        config = config || {};
        if (!data) {
            throw new Error("Cannot init K8S forced layout chart visualisation, invalid data given " + data);
        }
        var element = d3.select(selector),
            kinds = {
            Pod: '#vertex-Pod',
            ReplicationController: '#vertex-ReplicationController',
            Node: '#vertex-Node',
            Service: '#vertex-Service',
            ReplicaSet: '#vertex-ReplicaSet',
            Container: '#vertex-Container',
            Deployment: '#vertex-Deployment',
            Namespace: '#vertex-Namespace'
        };

        var graph = K8SVisualisations.forcedChart.constructChart(selector, { kinds: kinds });
        graph.render(graph.data(data["items"], data["relations"]), config);
        graph.select();
    };

    K8SVisualisations.forcedChart.constructChart = function (selector, options) {
        var outer = d3.select(selector);
        /* Kinds of objects to show */
        var _kinds = options["kinds"];
        /* Data we've been fed */
        var items = [];
        var relations = [];
        /* Graph information */
        var width;
        var height;
        var radius = 20;
        if (options["radius"]) {
            radius = options["radius"];
        }
        var timeout;
        var nodes = [];
        var links = [];
        var lookup = {};
        var selection = null;
        var force = options["force"];

        /* Allow the force to be passed in, default if not */
        if (!force) {
            force = d3.layout.force().charge(-60).linkDistance(100);
        }

        var drag = force.drag();

        var svg = outer.append("svg").attr("viewBox", "0 0 1600 1200").attr("preserveAspectRatio", "xMidYMid meet").attr("class", "kube-topology");
        var mouseFunctions = {
            linkOver: function linkOver(d) {
                svg.selectAll("line").classed("active", function (p) {
                    return p === d;
                });
                svg.selectAll(".node circle").classed("active", function (p) {
                    return p === d.source || p === d.target;
                });
                svg.selectAll(".node text").classed("active", function (p) {
                    return p === d.source || p === d.target;
                });
            },
            nodeOver: function nodeOver(d) {
                svg.selectAll("line").classed("active", function (p) {
                    return p.source === d || p.target === d;
                });
                d3.select(this).select("circle").classed("active", true);
                d3.select(this).select("text").classed("active", true);
            },
            out: function out(d) {
                svg.selectAll(".active").classed("active", false);
            }
        };
        // null values here
        var vertices = d3.select();
        var edges = d3.select();
        force.on("tick", function () {
            edges.attr("x1", function (d) {
                return d.source.x;
            }).attr("y1", function (d) {
                return d.source.y;
            }).attr("x2", function (d) {
                return d.target.x;
            }).attr("y2", function (d) {
                return d.target.y;
            });

            vertices.attr("cx", function (d) {
                d.x = d.fixed ? d.x : Math.max(radius, Math.min(width - radius, d.x));
                return d.x;
            }).attr("cy", function (d) {
                d.y = d.fixed ? d.y : Math.max(radius, Math.min(height - radius, d.y));
                return d.y;
            }).attr("transform", function (d) {
                return "translate(" + d.x + "," + d.y + ")";
            });
        });

        drag.on("dragstart", function (d) {
            select(d.item);

            if (d.fixed !== true) d.floatpoint = [d.x, d.y];
            d.fixed = true;
            d3.select(this).classed("fixed", true);
        }).on("dragend", function (d) {
            var moved = true;
            if (d.floatpoint) {
                moved = d.x < d.floatpoint[0] - 5 || d.x > d.floatpoint[0] + 5 || d.y < d.floatpoint[1] - 5 || d.y > d.floatpoint[1] + 5;
                delete d.floatpoint;
            }
            d.fixed = moved && d.x > 3 && d.x < width - 3 && d.y >= 3 && d.y < height - 3;
            d3.select(this).classed("fixed", d.fixed);
        });

        svg.on("dblclick", function () {
            svg.selectAll("g").classed("fixed", false).each(function (d) {
                d.fixed = false;
            });
            force.start();
        });

        function select(item) {
            selection = item;
            svg.selectAll("g").classed("selected", function (d) {
                return d.item === item;
            });
        }

        function adjust() {
            timeout = null;
            width = outer.node().clientWidth;
            height = outer.node().clientHeight;

            force.size([width, height]);
            svg.attr("viewBox", "0 0 " + width + " " + height);
            update();
        }

        function update() {
            edges = svg.selectAll("line").data(links);

            edges.exit().remove();
            edges.enter().insert("line", ":first-child");
            edges.attr("class", function (d) {
                return d.kinds;
            });
            edges.on("mouseover", mouseFunctions.linkOver).on("mouseout", mouseFunctions.out);

            vertices = svg.selectAll("g").data(nodes, function (d) {
                return d.id;
            });
            vertices.on("mouseover", mouseFunctions.nodeOver).on("mouseout", mouseFunctions.out);
            vertices.exit().remove();

            var added = vertices.enter().append("g").call(drag);

            select(selection);

            force.nodes(nodes).links(links).start();

            return added;
        }

        function digest() {
            var pnodes = nodes;
            var plookup = lookup;

            /* The actual data for the graph */
            nodes = [];
            links = [];
            lookup = {};

            var item, id, kind, node;
            for (id in items) {
                item = items[id];
                kind = item.kind;

                if (_kinds && !_kinds[kind]) continue;

                /* Prevents flicker */
                node = pnodes[plookup[id]];
                if (!node) {
                    node = K8SVisualisations.forcedChart.cache[id];
                    delete K8SVisualisations.forcedChart.cache[id];
                    if (!node) node = {};
                }

                node.id = id;
                node.item = item;

                lookup[id] = nodes.length;
                nodes.push(node);
            }

            var i, len, relation, s, t;
            for (i = 0, len = relations.length; i < len; i++) {
                relation = relations[i];

                s = lookup[relation.source];
                t = lookup[relation.target];
                if (s === undefined || t === undefined) continue;

                links.push({ source: s, target: t, kinds: nodes[s].item.kind + nodes[t].item.kind });
            }

            if (width && height) return update();else return d3.select();
        }

        function resized() {
            window.clearTimeout(timeout);
            timeout = window.setTimeout(adjust, 150);
        }
        window.addEventListener('resize', resized);
        adjust();
        resized();

        return {
            select: select,
            kinds: function kinds(value) {
                _kinds = value;
                var added = digest();
                return [vertices, added];
            },
            data: function data(new_items, new_relations) {
                items = new_items || {};
                relations = new_relations || [];
                var added = digest();
                return [vertices, added];
            },
            render: function render(graphData, config) {
                config = config || {};
                var vertices = graphData[0];
                var added = graphData[1];

                added.attr("class", function (d) {
                    return d.item.kind;
                });
                added.append("use").attr("xlink:href", function (d) {
                    return _kinds[d.item.kind];
                });
                added.append("title");
                if (config.hasOwnProperty("nodeClickFn") && typeof config.nodeClickFn === 'function') {
                    vertices.on("click", config.nodeClickFn);
                }
                vertices.selectAll("title").text(function (d) {
                    return d.item.metadata.name;
                });

                vertices.classed("weak", function (d) {
                    var status = d.item.status;
                    if (status && status.phase && status.phase !== "Running") return true;
                    return false;
                });
            },
            close: function close() {
                window.removeEventListener('resize', resized);
                window.clearTimeout(timeout);

                /*
                 * Keep the positions of these items cached,
                 * in case we are asked to make the same graph again.
                 */
                var id, node;
                K8SVisualisations.forcedChart.cache = {};
                for (id in lookup) {
                    node = nodes[lookup[id]];
                    delete node.item;
                    K8SVisualisations.forcedChart.cache[id] = node;
                }

                nodes = [];
                lookup = {};
            }
        };
    };

    return K8SVisualisations;
}(K8SVisualisations || {});
"use strict";

var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

Math.radians = function (degrees) {
    return degrees * Math.PI / 180;
};

// Converts from radians to degrees.
Math.degrees = function (radians) {
    return radians * 180 / Math.PI;
};
/**
 * Module with K8SVisualisations hive chart
 */
var K8SVisualisations = function (K8SVisualisations) {
    K8SVisualisations.hiveChart = K8SVisualisations.hiveChart || {};

    K8SVisualisations.hiveChart.init = function (selector, data, config) {
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
        }, {
            x: 1,
            angle: 270,
            radius: 200,
            name: "Nodes",
            kind: "Node"
        }, {
            x: 2,
            angle: 150,
            radius: 240,
            name: "Services",
            kind: "Service"
        }, {
            x: 3,
            angle: 210,
            radius: 240,
            name: "Deployments",
            kind: "Deployment"
        }, {
            x: 4,
            angle: 90,
            radius: 240,
            name: "Namespaces",
            kind: "Namespace"
        }],
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
            createNodes = function createNodes(items) {
            return items.map(function (item) {
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
            createLinks = function createLinks(nodes, relations) {
            return relations.map(function (link) {
                var retLink = {};
                nodes.forEach(function (node) {
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

        if (_typeof(data.items) === 'object') {
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

        var angle = function angle(d) {
            var angle = 0,
                found = false;
            axes.forEach(function (item) {
                if (d.kind == item.kind) {
                    angle = item.angle;
                    found = true;
                }
            });
            if (!found) {
                console.log("Cannot compute angle for item " + d.kind + d.metadata.name);
            }
            return angle;
        };
        var radius = d3.scale.linear().range([innerRadius, outerRadius]);
        var icon = function icon(i) {
            return icon_mapping[i];
        };
        var color = function color(i) {
            return color_mapping[i];
        };

        var mouseFunctions = {
            linkOver: function linkOver(d) {
                svg.selectAll(".link").classed("active", function (p) {
                    return p === d;
                });
                svg.selectAll(".node circle").classed("active", function (p) {
                    return p === d.source || p === d.target;
                });
                svg.selectAll(".node text").classed("active", function (p) {
                    return p === d.source || p === d.target;
                });
                //NodeMouseFunctions.over();
            },
            nodeOver: function nodeOver(d) {
                svg.selectAll(".link").classed("active", function (p) {
                    return p.source === d || p.target === d;
                });
                d3.select(this).select("circle").classed("active", true);
                d3.select(this).select("text").classed("active", true);
                tooltip.html("Node - " + d.name + "<br/>" + "Kind - " + d.kind).style("left", d3.event.pageX + 5 + "px").style("top", d3.event.pageY - 28 + "px");
                tooltip.transition().duration(200).style("opacity", .9);
            },
            out: function out(d) {
                svg.selectAll(".active").classed("active", false);
                tooltip.transition().duration(500).style("opacity", 0);
            }
        };

        var svg = d3.select(selector).append("svg").attr("width", width).attr("height", height).append("g").attr("transform", "translate(" + (width / 2 - 180) + "," + (height / 2 - 20) + ")");

        var tooltip = d3.select("body").append("div").attr("class", "tooltip").style("opacity", 0);

        // Hive plot render

        var axe = svg.selectAll(".node").data(axes).enter().append("g");

        axe.append("line").attr("class", "axis").attr("transform", function (d) {
            return "rotate(" + d.angle + ")";
        }).attr("x1", function (d) {
            return radius_mapping[d.kind].range()[0];
        }).attr("x2", function (d) {
            return radius_mapping[d.kind].range()[1];
        });

        axe.append("text").attr("class", "axis-label").attr('font-size', '16px').attr('font-family', 'Open Sans').attr('text-anchor', 'middle').attr('alignment-baseline', 'central').text(function (d) {
            return d.name;
        }).attr("transform", function (d) {
            var x = (radius_mapping[d.kind].range()[1] + 30) * Math.cos(Math.radians(d.angle));
            var y = (radius_mapping[d.kind].range()[1] + 30) * Math.sin(Math.radians(d.angle));
            return "translate(" + x + ", " + y + ")";
        });

        svg.selectAll(".link").data(links).enter().append("path").attr("class", "link").attr("d", d3.hive.link().angle(function (d) {
            return Math.radians(angle(d));
        }).radius(function (d) {
            return radius_mapping[d.kind](d.y * itemStep[d.kind] - 0.1);
        }))
        //.style("stroke", function(d) { return color(d.source.kind); })
        .on("mouseover", mouseFunctions.linkOver).on("mouseout", mouseFunctions.out);

        var node = svg.selectAll(".node").data(nodes).enter().append("g").attr("class", "node").attr("transform", function (d) {
            var x = radius_mapping[d.kind](d.y * itemStep[d.kind] - 0.1) * Math.cos(Math.radians(angle(d)));
            var y = radius_mapping[d.kind](d.y * itemStep[d.kind] - 0.1) * Math.sin(Math.radians(angle(d)));
            return "translate(" + x + ", " + y + ")";
        }).on("mouseover", mouseFunctions.nodeOver).on("mouseout", mouseFunctions.out);

        if (config.hasOwnProperty("nodeClickFn") && typeof config.nodeClickFn === 'function') {
            node.on("click", config.nodeClickFn);
        }

        node.append("use").attr("xlink:href", function (d) {
            return icon(d.kind);
        });
    };
    return K8SVisualisations;
}(K8SVisualisations || {});
'use strict';

function topology_data_transform(clusterData) {

  var relations = [];

  // Basic Transformation Array > Object with UID as Keys
  var transformedData = clusterData.reduce(function (acc, cur) {
    acc[cur.metadata.uid] = cur;
    return acc;
  }, {});

  // Add Containers as top-level resource
  var resource = void 0;
  for (resource in transformedData) {
    resource = transformedData[resource];
    if (resource.kind === 'Pod') {
      var _iteratorNormalCompletion = true;
      var _didIteratorError = false;
      var _iteratorError = undefined;

      try {
        for (var _iterator = resource.spec.containers[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
          var container = _step.value;

          var containerId = resource.metadata.uid + '-' + container.name;
          transformedData[containerId] = {};
          transformedData[containerId].metadata = container;
          transformedData[containerId].kind = 'Container';

          // Add to relations
          relations.push({ target: containerId, source: resource.metadata.uid });
        }
      } catch (err) {
        _didIteratorError = true;
        _iteratorError = err;
      } finally {
        try {
          if (!_iteratorNormalCompletion && _iterator.return) {
            _iterator.return();
          }
        } finally {
          if (_didIteratorError) {
            throw _iteratorError;
          }
        }
      }
    }
  }

  var item = void 0,
      kind = void 0;

  var _iteratorNormalCompletion2 = true;
  var _didIteratorError2 = false;
  var _iteratorError2 = undefined;

  try {
    for (var _iterator2 = clusterData[Symbol.iterator](), _step2; !(_iteratorNormalCompletion2 = (_step2 = _iterator2.next()).done); _iteratorNormalCompletion2 = true) {
      item = _step2.value;

      kind = item.kind;
      if (kind === 'Pod') {
        (function () {
          var pod = item;
          // define relationship between pods and nodes
          var podsNode = clusterData.find(function (i) {
            return i.metadata.name === pod.spec.nodeName;
          });
          if (podsNode) {
            relations.push({ source: pod.metadata.uid, target: podsNode.metadata.uid });
          } else {
            console.log("Cannot found pods node!");
          }
          // define relationships between pods and rep sets and replication controllers
          if (pod.metadata.ownerReferences) {
            var ownerReferences = pod.metadata.ownerReferences[0].uid;
            var podsRepController = clusterData.find(function (i) {
              return i.metadata.uid === ownerReferences;
            });
            relations.push({ target: pod.metadata.uid, source: podsRepController.metadata.uid });
          } else {
            console.log("Cannot found owner references!");
          }

          // rel'n between pods and services
          var podsService = clusterData.find(function (i) {
            if (i.kind === 'Service' && i.spec.selector) {
              return i.spec.selector.run === pod.metadata.labels.run;
            }
          });
          relations.push({ target: pod.metadata.uid, source: podsService.metadata.uid });
        })();
      }

      if (kind === 'Service') {
        var podsService = void 0;
        // console.log('item', item)
        // console.log(item.spec.selector)
      }

      if (kind === 'Deployment') {
        // console.log('item deployment', item)
      }
    }
  } catch (err) {
    _didIteratorError2 = true;
    _iteratorError2 = err;
  } finally {
    try {
      if (!_iteratorNormalCompletion2 && _iterator2.return) {
        _iterator2.return();
      }
    } finally {
      if (_didIteratorError2) {
        throw _iteratorError2;
      }
    }
  }

  var items = transformedData;
  return { items: items, relations: relations };
}