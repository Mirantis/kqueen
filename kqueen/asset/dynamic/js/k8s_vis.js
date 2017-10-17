var KubeTopologyVisualization = {
init: function(apiUrl) {
$(document).one("shown.bs.tab", "a[href='#topology']", function(e) {
  d3.json(apiUrl, function(data) {
    var selector = "#topology-graph"
     ,  element = d3.select(selector)
     ,  kinds = {
          Pod: '#vertex-Pod',
          ReplicationController: '#vertex-ReplicationController',
          Node: '#vertex-Node',
          Service: '#vertex-Service',
          ReplicaSet: '#vertex-ReplicaSet',
          Container: '#vertex-Container',
          Deployment: '#vertex-Deployment',
          Namespace: '#vertex-Namespace'
        };
        //element.css("display", "block");
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

            added.attr("class", function(d) { return d.item.kind; });
            added.append("use").attr("xlink:href", icon);
            added.append("title");
            vertices.on("click", function(d){
                    changeDetailBox(d);
            });
            vertices.selectAll("title")
                 .text(function(d) { return d.item.metadata.name; });

            vertices.classed("weak", weak);
            graph.select();
        }
        var graph = topology_graph(selector, notify, {kinds:kinds});
        render(graph.data(data["items"], data["relations"]));
        /* If there's a kinds in the current scope, watch it for changes
        $scope.$watchCollection("kinds", function(value) {
            render(graph.kinds(value));
        });

        $scope.$watchCollection('[items, relations]', function(values) {
        });

        /* Watch the selection for changes 
        $scope.$watch("selection", function(item) {
            graph.select(item || null);
        });

        element.on("$destroy", function() {
            graph.close();
        });*/
  });
});
}
};
