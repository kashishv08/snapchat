const defaultLat = 20.593684;
const defaultLng = 78.96288;

function initMap(lat, lng, isUserLocation) {
  const loader = document.getElementById("map-loader");
  if (loader) loader.style.display = "none";

  var map = L.map("map").setView([lat, lng], 13);

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);

  if (isUserLocation) {
    var marker = L.marker([lat, lng]).addTo(map);

    const reverseGeocodingUrl = `https://api.geoapify.com/v1/geocode/reverse?lat=${lat}&lon=${lng}&apiKey=${REVERSE_GEO_API_KEY}`;
    fetch(reverseGeocodingUrl)
      .then((result) => result.json())
      .then((featureCollection) => {
        if (
          featureCollection.features &&
          featureCollection.features.length > 0
        ) {
          const address = featureCollection.features[0].properties.formatted;
          console.log(address);
          marker.bindPopup(`<b>${address}</b>`).openPopup();
        }
      })
      .catch((error) =>
        console.error("Error fetching location details:", error),
      );
  }
}

if ("geolocation" in navigator) {
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;

      console.log(`Latitude: ${lat}, longitude: ${lng}`);
      initMap(lat, lng, true);
    },
    (error) => {
      console.error("Error getting user location:", error);
      console.log("Loading map with default location.");
      initMap(defaultLat, defaultLng, true);
    },
  );
} else {
  console.error("Geolocation is not supported by this browser.");
  initMap(defaultLat, defaultLng, false);
}
