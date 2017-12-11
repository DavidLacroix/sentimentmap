var d3 = Plotly.d3;

var mymap = L.map('mapid').setView([53.5, -6], 6);

// One group per custom layer
var data_group = L.featureGroup().addTo(mymap);

var map_url = 'https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png';
var map_attribution = '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>';
L.tileLayer(map_url, {attribution: map_attribution, maxZoom: 19}).addTo(mymap);

var minimap_layer = L.tileLayer(map_url, {attribution: map_attribution});
var minimap = new L.Control.MiniMap(minimap_layer, {
    zoomLevelOffset: -7,
    toggleDisplay: true,
    position: 'bottomleft',
    width: 300
}).addTo(mymap);


var pos_marker_options = {
    radius: 4,
    fillColor: "#28A745",//#00cc00
    color: "#28A745",//#00bb00
    weight: 1,
    opacity: 0.6,
    fillOpacity: 0.4
};

var neg_marker_options = {
    radius: 4,
    fillColor: "#DC3545",//#cc0000
    color: "#DC3545",//#bb0000
    weight: 1,
    opacity: 0.6,
    fillOpacity: 0.4
};

function on_each_feature(feature, layer) {
    if (feature.properties && feature.properties.text) {
        var pos = feature.properties.pos;
        var neu = feature.properties.neu;
        var neg = feature.properties.neg;
        
        var str_pos = Math.round(pos * 100) > 10 ? Math.round(pos * 10000) / 100 : "";
        var str_neu = Math.round(neu * 100) > 10 ? Math.round(neu * 10000) / 100 : "";
        var str_neg = Math.round(neg * 100) > 10 ? Math.round(neg * 10000) / 100 : "";
        
        var sentiment_bar = `
            <div style="height: 22px; width: 100%;">
                <div class="bg-success" style="float: left; height: 100%; width: ${Math.round(pos * 98)}%; border: solid 2px white; border-radius: 6px; text-align: center;font-weight: bold;">${str_pos}</div>
                <div class="bg-warning" style="float: left; height: 100%; width: ${Math.round(neu * 98)}%; border: solid 2px white; border-radius: 6px; text-align: center;font-weight: bold;">${str_neu}</div>
                <div class="bg-danger" style="float: left; height: 100%; width: ${Math.round(neg * 98)}%; border: solid 2px white; border-radius: 6px; text-align: center;font-weight: bold;">${str_neg}</div>
            </div>
        `;
        
        layer.bindPopup(sentiment_bar + '<span style="font-weight: bold">' + feature.properties.created_at + '</span></br>' + feature.properties.text);
    }
}

function search_tweet(search, accuracy){
    var SW = mymap.getBounds().getSouthWest();
    var NE = mymap.getBounds().getNorthEast();
    $.ajax({
        url: 'tweet',
        data: {'search': search, 'accuracy': accuracy,'SWlon': SW.lng, 'SWlat': SW.lat, 'NElon': NE.lng, 'NElat': NE.lat},
        dataType: 'json',
        type: 'GET',
        success: function(response) {
            var data = response.data;
            for (i in data){
                record = data[i];
                
                if(record['properties']['compound'] > 0){
                    L.geoJSON(record, {
                        onEachFeature: on_each_feature,
                        pointToLayer: function (feature, latlng) {
                            return L.circleMarker(latlng, pos_marker_options);
                        }
                    }).addTo(data_group);
                } else {
                    L.geoJSON(record, {
                        onEachFeature: on_each_feature,
                        pointToLayer: function (feature, latlng) {
                            return L.circleMarker(latlng, neg_marker_options);
                        }
                    }).addTo(data_group);
                }
            }
            $('#search-tweet').prop('disabled', false);
            
            if(data.length > 0){
                feed_info_popover(search, response.stats);
                $('#info').prop('disabled', false);
            }
            
        }
    });
}

function feed_info_popover(search, stats){
    $('#info').attr('data-original-title', 'Info for search: "<i>'+search+'</i>"');
    var html_content = `
        <table class="table table-sm">
          <tbody>
            <tr>
              <td>Tweet count</td>
              <td>${stats.total}</td>
            </tr>
            <tr>
              <td>Avg sentiment</td>
              <td>${Math.round(stats.mean_compound * 100) / 100}</td>
            </tr>
            <tr>
              <td>Pop std dev</td>
              <td>${Math.round(stats.pop_std_dev * 100) / 100}</td>
            </tr>
          </tbody>
        </table>
    `;
    
    $('#info').attr('data-content',html_content);
    
}

$('#search-tweet').click(function() {
    $(this).prop('disabled', true);
    $('#info').popover('hide');
    $('#info').prop('disabled', true);
    data_group.clearLayers();
    var search = $("#search-tweet-input").val();
    var accuracy = $("#search-accuracy").find("option:selected").val();
    search_tweet(search, accuracy);
});

$('#reset').click(function() {
    $('#info').prop('disabled', true);
    $('#info').popover('hide')
    $('#search-tweet-input').val("");
    data_group.clearLayers();
    mymap.setView([53.5, -6], 6);
});


$(document).keypress(function(e) {
    if(e.which === 13) {
        e.preventDefault();
        if($("#search-tweet").prop('disabled') === false){
            $("#search-tweet").first().click();
        }
        
    }
});

$(function () {
    
  $('[data-toggle="tooltip"]').tooltip();
  $('#info').popover({
    animation: true,
    placement: 'bottom',
    html: true
  })
  $('#info').prop('disabled', true);
  
})
