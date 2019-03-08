<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no">
  <title>Search Widget - 4.10</title>

  <style>
    html,
    body,
    #viewDiv {
      padding: 0;
      margin: 0;
      height: 100%;
      width: 100%;
    }
  </style>

  <link rel="stylesheet" href="https://js.arcgis.com/4.10/esri/css/main.css">
  <script src="https://js.arcgis.com/4.10/"></script>

  <script>
    require([
      "esri/Map",
      "esri/views/SceneView",
      "esri/widgets/Search",
      "esri/widgets/Search/LocatorSearchSource",
      "esri/core/Collection",
       "esri/tasks/Locator"
    ], function(
      Map,
      SceneView,
      Search,LocatorSearchSource,
      Collection,
      Locator) {

      var map = new Map({
        basemap: "satellite",
        ground: "world-elevation"
      });

      var view = new SceneView({
        zoom:13,
        container: "viewDiv",
        center: [-104.855469,39.594525],
        map: map
      });

  var searchWidget = new Search({
    sources: [{
      locator: new Locator({ url: "https://utility.arcgis.com/usrsvcs/servers/abb3dfccf5314ae48bd67ee047cb84ac/rest/services/World/GeocodeServer"}),
      //countryCode:"USA",
      //category:"en-co",
      singleLineFieldName: "SingleLine",
      name: "Custom Geocoding Service",
      localSearchOptions: {
        minScale: 3000,
        distance: 50000
      },
      placeholder: "Search USA",
      maxResults: 3,
      maxSuggestions: 6,
      suggestionsEnabled: true,
      minSuggestCharacters: 0
  }],
    view: view,
    includeDefaultSources: false
  });

  // Add the search widget to the top right corner of the view
  view.ui.add(searchWidget, {
    position: "top-right"
  });
    });
  </script>
</head>

<body>
  <div id="viewDiv"></div>
</body>

</html>
