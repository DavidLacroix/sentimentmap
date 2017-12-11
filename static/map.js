var mymap = L.map('mapid').setView([53.5, -6], 6);
//var mymap = L.map('mapid').setView([51.50, -0.13], 11);

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
    fillColor: "#00cc00",
    color: "#00bb00",
    weight: 1,
    opacity: 0.6,
    fillOpacity: 0.4
};

var neg_marker_options = {
    radius: 4,
    fillColor: "#cc0000",
    color: "#bb0000",
    weight: 1,
    opacity: 0.6,
    fillOpacity: 0.4
};

function on_each_feature(feature, layer) {
    if (feature.properties && feature.properties.text) {
        layer.bindPopup('[' + feature.properties.created_at + '] ' + feature.properties.text);
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
        success: function(data) {
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
        }
    });
}

$('#search-tweet').click(function() {
    $(this).prop('disabled', true);
    data_group.clearLayers();
    var search = $("#search-tweet-input").val();
    var accuracy = $("#search-accuracy").find("option:selected").val();
    search_tweet(search, accuracy);
});

$('#reset').click(function() {
    data_group.clearLayers();
    mymap.setView([53.5, -6], 6);
});

$(function () {
  $('[data-toggle="tooltip"]').tooltip();
})