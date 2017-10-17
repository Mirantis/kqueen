/**
 * Module with K8SVisualisations forced chart
 */
var K8SVisualisations = function(K8SVisualisations) {
    K8SVisualisations.forcedChart = K8SVisualisations.forcedChart || {};

    K8SVisualisations.forcedChart.init = function(selector, data) {
        selector = selector || "#topology-graph"
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

        function notify(item) {
            graph.select(item);
        }

        function icon(d) {
            return kinds[d.item.kind];
        }

        function weak(d) {
            var status = d.item.status;
            if (status && status.phase && status.phase !== "Running")
                return true;
            return false;
        }

        function title(d) {
            return d.item.metadata.name;
        }

        function render(args) {
            var vertices = args[0];
            var added = args[1];

            added.attr("class", function(d) {
                return d.item.kind;
            });
            added.append("use").attr("xlink:href", icon);
            added.append("title");
            vertices.on("click", function(d) {
                changeDetailBox(d);
            });
            vertices.selectAll("title")
                .text(function(d) {
                    return d.item.metadata.name;
                });

            vertices.classed("weak", weak);
            graph.select();
        }
        var graph = topology_graph(selector, notify, {kinds: kinds});
        render(graph.data(data["items"], data["relations"]));
    }
    return K8SVisualisations;
}(K8SVisualisations || {});