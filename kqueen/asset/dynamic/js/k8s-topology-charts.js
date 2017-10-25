 /**
 * Module with K8SVisualisations main init
 */
var K8SVisualisations = function(K8SVisualisations) {
    K8SVisualisations = K8SVisualisations || {};

    K8SVisualisations.init = function(topologyDataURL) {
       // init Isotope
      $(document).one("shown.bs.tab", "a[href='#addons']", function(e) {
        var $grid = $('.grid').isotope({
          itemSelector: '.addon-item',
          layoutMode: 'fitRows'
        });
        $('.grid').each(function() {
          var $grid = $( this );
          $grid.css('min-height', $grid.innerHeight());
        });
        // bind filter button click
        $('#filters').on( 'click', 'a', function(ev) {
        ev.preventDefault();
        var filterValue = $( this ).attr('data-filter');
          $grid.isotope({ filter: filterValue });
        });
      });
      $(function(){
        // init Clipboard
        // TODO: failing new Clipboard('.clipboard');
        // init asPieProgress
        $('.pie_progress').asPieProgress({
          namespace: 'pieProgress',
          barsize: '1',
          size: '120',
          min: 0,
          trackcolor: '#ececea',
          barcolor: '#4bbfaf',
          numberCallback(n) {
            return n;
          }
        });
        $('.pie_progress').asPieProgress('start');

        // bind click actions
        $("#ForcedLayoutGraphBtn").on("click",function (e){
          $("#HiveGraphContainer").css("z-index","1").css("pointer-events","none");
          $("#ForcedLayoutGraphContainer").css("z-index","2").css("pointer-events","all");
          $("#HiveGraphBtn").removeClass("active");
          $("#ForcedLayoutGraphBtn").addClass("active");
        });

        $("#HiveGraphBtn").on("click",function (e){
          $("#ForcedLayoutGraphContainer").css("z-index","1").css("pointer-events","none");
          $("#HiveGraphContainer").css("z-index","2").css("pointer-events","all");
          $("#ForcedLayoutGraphBtn").removeClass("active")
          $("#HiveGraphBtn").addClass("active");
        });
        $(".topology-legend svg").each(function(){
          var filterData = function(data, filterState){
            var enabledKinds = Object.entries(filterState).filter(function(i){return i[1]}).map(function(i){return i[0]})
             ,  newItems = {};
             // filter entries by kind
            Object.entries(window._originalGraphData.items).forEach(function(i){
              if(enabledKinds.indexOf(i[1].kind) != -1){
                newItems[i[0]] = i[1];
              }
            });
            return {items: newItems, kinds: window._originalGraphData.kinds, relations: window._originalGraphData.relations};
          };

          $(this).on("click", function(e){
            $(e.target).parent().toggleClass("filterDisabled")
            var filterState = {};
            $(".topology-legend svg").each(function(){
                var $chbox = $(this);
                filterState[$chbox.attr("data-kind")]=!$chbox.hasClass("filterDisabled");
            });
            initCharts(filterData(window._originalGraphData, filterState));
          });
        });
      });

      var initCharts = function(data){
            var changeDetailBox =function (node){
              console.log(node);
              if ('item' in node) {
                $('#resource-detail').html("<dl><dt>Name</dt><dd>" + node.item.metadata.name + "</dd><dt>Kind</dt><dd>" + node.item.kind + "</dd><dt>Namespace</dt><dd>" + node.item.metadata.namespace + "</dd></dl>");
              } else {
                $('#resource-detail').html("<dl><dt>Name</dt><dd>" + node.metadata.name + "</dd><dt>Kind</dt><dd>" + node.kind + "</dd><dt>Namespace</dt><dd>" + node.metadata.namespace + "</dd></dl>");
              }
            };
            if(data){
              window._graphData = data;
            }
            K8SVisualisations.forcedChart.init("#topology-graph",  $.extend({}, window._graphData), {nodeClickFn: changeDetailBox});
            K8SVisualisations.hiveChart.init("#HiveChart",  $.extend({}, window._graphData), {nodeClickFn: changeDetailBox});
            $("#HiveGraphBtn, #ForcedLayoutGraphBtn").attr("disabled", false);
      };

      $(document).one("shown.bs.tab", "a[href='#topology']", function(e) {
        d3.json(topologyDataURL, function(data){
          window._originalGraphData = data;
          initCharts(data);
        });
      });
  };
  return K8SVisualisations;
}(K8SVisualisations || {});