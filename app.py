<!-- index.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Room Temperature Status</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    /* Map is always visible */
    #map { height: 560px; width: 100%; display: block; }
    .leaflet-popup-content-wrapper { border-radius: 12px; background: #fffaf5; }
  </style>
</head>
<body>
  <h1>🌡️ Room Temperature</h1>
  
  <!-- PLC1 Section -->
  <div style="margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9;">
    <h2>PLC1 (Toronto)</h2>
    <div style="margin-bottom: 10px;">
      <label for="plc1-actual-temp">Actual Temperature (°C):</label>
      <input type="number" id="plc1-actual-temp" placeholder="Enter actual temperature" step="0.1" style="padding: 5px; margin-left: 10px; width: 150px;">
      <button onclick="setPLCActualTemp('PLC1')" style="padding: 5px 15px; margin-left: 10px; cursor: pointer;">Set Actual Temp</button>
    </div>
    <div style="margin-bottom: 10px;">
      <label for="plc1-setpoint">Setpoint (°C):</label>
      <input type="number" id="plc1-setpoint" placeholder="Enter setpoint" step="0.1" style="padding: 5px; margin-left: 10px; width: 150px;">
      <button onclick="setPLCSetpoint('PLC1')" style="padding: 5px 15px; margin-left: 10px; cursor: pointer;">Set Setpoint</button>
    </div>
    <div style="margin-bottom: 10px;">
      <label for="plc1-threshold">Threshold (°C):</label>
      <input type="number" id="plc1-threshold" placeholder="Enter threshold" step="0.1" style="padding: 5px; margin-left: 10px; width: 150px;">
      <button onclick="setPLCThreshold('PLC1')" style="padding: 5px 15px; margin-left: 10px; cursor: pointer;">Set Threshold</button>
    </div>
    <p id="plc1-temp">Current: Loading PLC1 data...</p>
    <p id="plc1-warning" style="color: red; font-weight: bold; display: none; margin-top: 10px;">⚠️ WARNING: Current temperature is HIGHER than threshold!</p>
  </div>

  <!-- PLC2 Section -->
  <div style="margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9;">
    <h2>PLC2 (Vancouver)</h2>
    <div style="margin-bottom: 10px;">
      <label for="plc2-actual-temp">Actual Temperature (°C):</label>
      <input type="number" id="plc2-actual-temp" placeholder="Enter actual temperature" step="0.1" style="padding: 5px; margin-left: 10px; width: 150px;">
      <button onclick="setPLCActualTemp('PLC2')" style="padding: 5px 15px; margin-left: 10px; cursor: pointer;">Set Actual Temp</button>
    </div>
    <div style="margin-bottom: 10px;">
      <label for="plc2-setpoint">Setpoint (°C):</label>
      <input type="number" id="plc2-setpoint" placeholder="Enter setpoint" step="0.1" style="padding: 5px; margin-left: 10px; width: 150px;">
      <button onclick="setPLCSetpoint('PLC2')" style="padding: 5px 15px; margin-left: 10px; cursor: pointer;">Set Setpoint</button>
    </div>
    <div style="margin-bottom: 10px;">
      <label for="plc2-threshold">Threshold (°C):</label>
      <input type="number" id="plc2-threshold" placeholder="Enter threshold" step="0.1" style="padding: 5px; margin-left: 10px; width: 150px;">
      <button onclick="setPLCThreshold('PLC2')" style="padding: 5px 15px; margin-left: 10px; cursor: pointer;">Set Threshold</button>
    </div>
    <p id="plc2-temp">Current: Loading PLC2 data...</p>
    <p id="plc2-warning" style="color: red; font-weight: bold; display: none; margin-top: 10px;">⚠️ WARNING: Current temperature is HIGHER than threshold!</p>
  </div>

  <!-- Setpoint Controls -->
  <div style="margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
    <h3>Set Temperature Setpoints</h3>
    <div style="margin-bottom: 10px;">
      <label for="setpoint-plc1">PLC1 Setpoint (°C):</label>
      <input type="number" id="setpoint-plc1" placeholder="Enter PLC1 setpoint" step="0.1" style="padding: 5px; margin-left: 10px; width: 120px;">
      <button onclick="setPLCSetpoint('PLC1')" style="padding: 5px 15px; margin-left: 10px; cursor: pointer;">Set PLC1</button>
    </div>
    <div>
      <label for="setpoint-plc2">PLC2 Setpoint (°C):</label>
      <input type="number" id="setpoint-plc2" placeholder="Enter PLC2 setpoint" step="0.1" style="padding: 5px; margin-left: 10px; width: 120px;">
      <button onclick="setPLCSetpoint('PLC2')" style="padding: 5px 15px; margin-left: 10px; cursor: pointer;">Set PLC2</button>
    </div>
  </div>

  <script>
    function setPLCActualTemp(plc) {
      const inputId = plc === 'PLC1' ? 'plc1-actual-temp' : 'plc2-actual-temp';
      const input = document.getElementById(inputId);
      const temp = parseFloat(input.value);
      
      if (isNaN(temp)) {
        alert(`Please enter a valid temperature for ${plc}`);
        return;
      }
      
      // Send actual temperature to backend
      fetch("https://temperature-server.onrender.com/temperature/manual/" + plc.toLowerCase(), {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          temperature: temp
        })
      })
      .then(res => res.json())
      .then(data => {
        console.log(`${plc} actual temperature response:`, data);
        if (data.status === "success") {
          alert(`${plc} actual temperature set to ${temp}°C`);
          input.value = '';
          // Refresh data to show updated temperature
          fetchPLCData();
        } else {
          alert(`Error setting ${plc} actual temperature: ${data.message}`);
        }
      })
      .catch(err => {
        console.error(`Error setting ${plc} actual temperature:`, err);
        alert(`Error setting ${plc} actual temperature`);
      });
    }

    function setPLCThreshold(plc) {
      const inputId = plc === 'PLC1' ? 'plc1-threshold' : 'plc2-threshold';
      const input = document.getElementById(inputId);
      const threshold = parseFloat(input.value);
      
      if (isNaN(threshold)) {
        alert(`Please enter a valid threshold for ${plc}`);
        return;
      }
      
      // Send threshold to backend
      fetch("https://temperature-server.onrender.com/threshold/" + plc.toLowerCase(), {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          threshold: threshold
        })
      })
      .then(res => res.json())
      .then(data => {
        console.log(`${plc} threshold response:`, data);
        if (data.status === "success") {
          alert(`${plc} threshold set to ${threshold}°C`);
          input.value = '';
          // Refresh data to show updated threshold
          fetchPLCData();
        } else {
          alert(`Error setting ${plc} threshold: ${data.message}`);
        }
      })
      .catch(err => {
        console.error(`Error setting ${plc} threshold:`, err);
        alert(`Error setting ${plc} threshold`);
      });
    }

    function setPLCSetpoint(plc) {
      const inputId = plc === 'PLC1' ? 'plc1-setpoint' : 'plc2-setpoint';
      const input = document.getElementById(inputId);
      const setpoint = parseFloat(input.value);
      
      if (isNaN(setpoint)) {
        alert(`Please enter a valid setpoint for ${plc}`);
        return;
      }
      
      // Send setpoint to backend
      fetch("https://temperature-server.onrender.com/setpoint/" + plc.toLowerCase(), {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          setpoint: setpoint
        })
      })
      .then(res => res.json())
      .then(data => {
        console.log(`${plc} setpoint response:`, data);
        if (data.status === "success") {
          alert(`${plc} setpoint set to ${setpoint}°C`);
          input.value = '';
          // Refresh data to show updated setpoint
          fetchPLCData();
        } else {
          alert(`Error setting ${plc} setpoint: ${data.message}`);
        }
      })
      .catch(err => {
        console.error(`Error setting ${plc} setpoint:`, err);
        alert(`Error setting ${plc} setpoint`);
      });
    }

    function fetchPLCData() {
      fetch("https://temperature-server.onrender.com/plc-data")
        .then(res => {
          if (!res.ok) throw new Error('Network response not ok: ' + res.status);
          return res.json();
        })
        .then(data => {
          console.log('PLC data response', data);
          
          // Update PLC1 data
          updatePLCDisplay('PLC1', data.PLC1);
          
          // Update PLC2 data
          updatePLCDisplay('PLC2', data.PLC2);
        })
        .catch(err => {
          console.error('fetchPLCData error:', err);
          document.getElementById('plc1-temp').innerText = "Error fetching PLC1 data.";
          document.getElementById('plc2-temp').innerText = "Error fetching PLC2 data.";
        });
    }

    function updatePLCDisplay(plc, plcData) {
      const tempElementId = plc === 'PLC1' ? 'plc1-temp' : 'plc2-temp';
      const warningElementId = plc === 'PLC1' ? 'plc1-warning' : 'plc2-warning';
      
      const tempElement = document.getElementById(tempElementId);
      const warningElement = document.getElementById(warningElementId);
      
      const currentTemp = plcData.temperature;
      const setpoint = plcData.setpoint;
      const threshold = plcData.threshold;
      
      if (currentTemp !== "Not Available") {
        tempElement.innerText = `Current temperature: ${currentTemp}°C | Setpoint: ${setpoint}°C | Threshold: ${threshold}°C`;
        
        // Check if current temperature is greater than threshold
        const isAbove = parseFloat(currentTemp) > parseFloat(threshold);
        if (isAbove) {
          warningElement.style.display = 'block';
          // Show map and update appropriate marker
          showMapIfNeeded();
          updateMarkers(plc, true);
          // Send alert to backend
          sendTemperatureAlert(currentTemp, threshold, plc);
        } else {
          warningElement.style.display = 'none';
          updateMarkers(plc, false);
        }
      } else {
        tempElement.innerText = `${plc} data not available yet`;
        warningElement.style.display = 'none';
        updateMarkers(plc, false);
      }
    }

    function sendTemperatureAlert(currentTemp, setpoint, plc) {
      fetch("https://temperature-server.onrender.com/temperature/alert", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          current_temperature: currentTemp,
          threshold_temperature: setpoint
        })
      })
      .then(res => res.json())
      .then(data => {
        console.log(`${plc} alert response:`, data);
      })
      .catch(err => {
        console.error(`Error sending ${plc} alert:`, err);
    }

    // Fetch immediately on page load
    fetchPLCData();

    // Auto-refresh every 5 seconds
    setInterval(fetchPLCData, 5000);

    // Display the stored setpoint on page load and initialize the map (map always visible)
    window.onload = function() {
      // Initialize setpoint inputs with current values from backend
      fetch("https://temperature-server.onrender.com/threshold")
        .then(res => res.json())
        .then(data => {
          document.getElementById('setpoint-plc1').placeholder = `Current PLC1 setpoint: ${data.plc1_setpoint}°C`;
          document.getElementById('setpoint-plc2').placeholder = `Current PLC2 setpoint: ${data.plc2_setpoint}°C`;
          document.getElementById('plc1-setpoint').placeholder = `Current setpoint: ${data.plc1_setpoint}°C`;
          document.getElementById('plc1-threshold').placeholder = `Current threshold: ${data.plc1_threshold}°C`;
          document.getElementById('plc2-setpoint').placeholder = `Current setpoint: ${data.plc2_setpoint}°C`;
          document.getElementById('plc2-threshold').placeholder = `Current threshold: ${data.plc2_threshold}°C`;
        })
        .catch(err => {
          console.error('Error fetching thresholds:', err);
        });
      
      if (typeof initMap === 'function') initMap();
    };
  </script>

  <!-- Inlined Canada map -->
  <section style="margin-top: 30px;">
    <h2>🗺️ Canada Map (PLC Monitoring)</h2>
    <p style="margin-top:0; margin-bottom:8px; color:#555;">Map displays PLC1 (Toronto) and PLC2 (Vancouver) temperature alerts.</p>
    <div style="border:1px solid #ddd; border-radius:6px; overflow:hidden;">
      <div id="map"></div>
    </div>
    <p style="font-size:90%; color:#666; margin-top:8px;">If the map does not load, <a href="../Mapping/canada_map.html" target="_blank" rel="noopener">open it in a new tab</a>.</p>
  </section>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    // Initialize map and Toronto marker; called on window.onload
    let torontoMarker = null;
      let vancouverMarker = null;
    
    function initMap() {
      // If map already exists, do nothing (prevents double-initialize error)
      if (window.__leafletMap) return;

      const map = L.map('map', { zoomControl: false }).setView([56, -96], 4);
      // store global reference for later marker operations
      window.__leafletMap = map;

      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap, © CARTO'
      }).addTo(map);

        // Markers will be created lazily when needed
        torontoMarker = null;
      vancouverMarker = null;
    }

    // Legacy function - maintained for compatibility
    function updateTorontoMarker(isAbove) {
      // Maintained for backwards compatibility
    }
    
    // Helper to update markers based on PLC: blink yellow for 1s when `isAbove` true
    function updateMarkers(plcSource, isAbove) {
      // If below threshold, remove marker from map (if present)
      if (!isAbove) {
        if (plcSource === 'PLC1' || plcSource === 'plc1') {
          if (torontoMarker && torontoMarker.remove) {
            torontoMarker.remove();
            torontoMarker = null;
          }
        } else if (plcSource === 'PLC2' || plcSource === 'plc2') {
          if (vancouverMarker && vancouverMarker.remove) {
            vancouverMarker.remove();
            vancouverMarker = null;
          }
        }
        return;
      }

      // Above threshold: ensure map and marker exist
      showMapIfNeeded();
      
      if (plcSource === 'PLC1' || plcSource === 'plc1') {
        blinkMarker('toronto');
      } else if (plcSource === 'PLC2' || plcSource === 'plc2') {
        blinkMarker('vancouver');
      }
    }
    
    // Helper function to create and blink a marker
    function blinkMarker(location) {
      let marker = null;
      let coords = null;
      let title = null;
      
      if (location === 'toronto') {
        marker = torontoMarker;
        coords = [43.6532, -79.3832];
        title = 'Toronto (PLC1)';
      } else if (location === 'vancouver') {
        marker = vancouverMarker;
        coords = [49.2827, -123.1207];
        title = 'Vancouver (PLC2)';
      }
      
      if (!marker) {
        marker = L.circleMarker(coords, {
          radius: 12,
          fillColor: '#ffd43b', // start yellow for blink
          color: '#ffffff',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.9
        }).addTo(window.__leafletMap).bindPopup(`<strong>${title}</strong>`);
        
        if (location === 'toronto') {
          torontoMarker = marker;
        } else if (location === 'vancouver') {
          vancouverMarker = marker;
        }
      }

      // Blink: toggle visibility every 200ms for 1 second, then set to red
      let blinkCount = 0;
      const maxBlinks = 5; // 5 toggles == ~1s (200ms each)
      const originalFill = '#e63946';
      const blinkColor = '#ffd43b';

      const blinkInterval = setInterval(() => {
        if (!marker) {
          clearInterval(blinkInterval);
          return;
        }
        const visible = (blinkCount % 2) === 0;
        marker.setStyle({ fillColor: visible ? blinkColor : '#ffffff', fillOpacity: visible ? 0.9 : 0.0 });
        blinkCount += 1;
        if (blinkCount >= maxBlinks) {
          clearInterval(blinkInterval);
          // Final state: solid red and open popup
          if (marker) {
            marker.setStyle({ fillColor: originalFill, fillOpacity: 0.9 });
            marker.openPopup();
          }
        }
      }, 200);
    }

    // Show/hide map container (initialize map on first show)
    let mapInitialized = false;
    function showMapIfNeeded() {
      const mapEl = document.getElementById('map');
        if (!mapEl) return;
        if (!mapInitialized) {
          initMap();
          mapInitialized = true;
        }
    }

      function hideMap() {
        // Per requirement: do not hide the map. Only remove marker if present.
                if (vancouverMarker && vancouverMarker.remove) {
                  vancouverMarker.remove();
                  vancouverMarker = null;
                }
        if (torontoMarker && torontoMarker.remove) {
          torontoMarker.remove();
          torontoMarker = null;
        }
      }

    // Keep a global reference to the Leaflet map for marker creation
    // assigned in initMap
  </script>
</body>
</html>
