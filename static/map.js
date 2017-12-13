var d3 = Plotly.d3;

var mymap = L.map('mapid').setView([53.5, -6], 6);
var map_url = 'https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png';
var map_attribution = '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>';

// Setting up main map tile layer
var map_layer = L.tileLayer(map_url, {
    attribution: map_attribution, 
    maxZoom: 19
}).addTo(mymap);

// Settingup minimap for navigation in high zoom level
var minimap_layer = L.tileLayer(map_url, {
    attribution: map_attribution
});
var minimap = new L.Control.MiniMap(minimap_layer, {
    zoomLevelOffset: -7,
    toggleDisplay: true,
    position: 'bottomleft',
    width: 300
}).addTo(mymap);

// One group per custom layer
var data_group = L.featureGroup().addTo(mymap);

// Style for leaflet positive sentiment markers
var pos_marker_options = {
    radius: 4,
    fillColor: "#28A745",//#00cc00
    color: "#28A745",//#00bb00
    weight: 1,
    opacity: 0.6,
    fillOpacity: 0.4
};

// Style for leaflet negative sentiment markers
var neg_marker_options = {
    radius: 4,
    fillColor: "#DC3545",//#cc0000
    color: "#DC3545",//#bb0000
    weight: 1,
    opacity: 0.6,
    fillOpacity: 0.4
};

// Sentiment bar is a simple custom component to display a sentiment from VADER: |+++|========|----|
function create_sentiment_bar(pos, neu, neg, min_score_display){
    var display_pos = Math.round(pos * 100) > min_score_display ? Math.round(pos * 10000) / 100 : "";
    var display_neu = Math.round(neu * 100) > min_score_display ? Math.round(neu * 10000) / 100 : "";
    var display_neg = Math.round(neg * 100) > min_score_display ? Math.round(neg * 10000) / 100 : "";
    
    return `
        <div style="height: 26px; width: 100%;display:block;overflow:hidden; vertical-align: middle;line-height: 22px;">
            <div class="bg-success" style="float: left; height: 100%; width: ${Math.round(pos * 95)}%; border: solid 2px white; border-radius: 6px; text-align: center;font-weight: bold;">${display_pos}</div>
            <div class="bg-warning" style="float: left; height: 100%; width: ${Math.round(neu * 95)}%; border: solid 2px white; border-radius: 6px; text-align: center;font-weight: bold;">${display_neu}</div>
            <div class="bg-danger" style="float: left; height: 100%; width: ${Math.round(neg * 95)}%; border: solid 2px white; border-radius: 6px; text-align: center;font-weight: bold;">${display_neg}</div>
        </div>
    `;
}

function on_each_feature(feature, layer) {
    if (feature.properties && feature.properties.text) {
        var pos = feature.properties.pos;
        var neu = feature.properties.neu;
        var neg = feature.properties.neg;
        
        layer.bindPopup(create_sentiment_bar(pos, neu, neg, 10) + '<span style="font-weight: bold">' + feature.properties.created_at + '</span></br>' + feature.properties.text);
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
                
                if(record.properties.pos > record.properties.neg){
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
                feed_info_popover(search, response.meta);
                $('#info').prop('disabled', false);
            }
            
        }
    });
}

function feed_info_popover(search, meta){
    $('#info').attr('data-original-title', 'Info for search: "<i>'+search+'</i>"');
    var html_content = `
        ${create_sentiment_bar(meta.search_sentiment.pos, meta.search_sentiment.neu, meta.search_sentiment.neg, 20)}
        <table class="table table-sm mt-2 text-center">
          <thead class="thead-light">
            <tr>
              <th>#</th>
              <th>search</th>
              <th>total</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>count</td>
              <td>${meta['search-stats'].total}</td>
              <td>${meta['global-stats'].total}</td>
            </tr>
            <tr>
              <td>pos avg</td>
              <td>${Math.round(meta['search-stats'].mean_pos * 100) / 100}</td>
              <td>${Math.round(meta['global-stats'].mean_pos * 100) / 100}</td>
            </tr>
            <tr>
              <td>pos stddev</td>
              <td>${Math.round(meta['search-stats'].stddev_pos * 100) / 100}</td>
              <td>${Math.round(meta['global-stats'].stddev_pos * 100) / 100}</td>
            </tr>
            <tr>
              <td>neg avg</td>
              <td>${Math.round(meta['search-stats'].mean_neg * 100) / 100}</td>
              <td>${Math.round(meta['global-stats'].mean_neg * 100) / 100}</td>
            </tr>
            <tr>
              <td>neg stddev</td>
              <td>${Math.round(meta['search-stats'].stddev_neg * 100) / 100}</td>
              <td>${Math.round(meta['global-stats'].stddev_neg * 100) / 100}</td>
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
  
});
