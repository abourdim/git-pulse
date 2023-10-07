/* GitPulse i18n — lightweight translation loader */
(function(){
  var _lang = "en";
  var _strings = {};
  var _loaded = false;

  try { _lang = localStorage.getItem("gp_language") || "en"; } catch(e){}

  // Public translate function
  window.t = function(key, fallback){
    return _strings[key] || fallback || key;
  };

  // Apply translations to all data-i18n elements
  function apply(){
    document.querySelectorAll("[data-i18n]").forEach(function(el){
      var key = el.getAttribute("data-i18n");
      var val = _strings[key];
      if(!val) return;
      // Check target attribute
      var attr = el.getAttribute("data-i18n-attr");
      if(attr === "placeholder"){
        el.placeholder = val;
      } else if(attr === "title"){
        el.title = val;
      } else {
        // Preserve leading emoji/icon if present
        var text = el.textContent || "";
        var match = text.match(/^([\u2000-\u3300\uD83C-\uDBFF\uDC00-\uDFFF\uFE00-\uFEFF]+\s*|[^\w\s]\s*)/u);
        if(match && match[0].trim().length <= 2){
          el.textContent = match[0] + val;
        } else {
          el.textContent = val;
        }
      }
    });
    _loaded = true;
  }

  // Load and apply
  function load(lang){
    _lang = lang || _lang;
    fetch("/static/i18n/" + _lang + ".json")
      .then(function(r){ return r.json(); })
      .then(function(data){
        _strings = data;
        apply();
      })
      .catch(function(){
        // Fallback to English
        if(_lang !== "en"){
          _lang = "en";
          load("en");
        }
      });
  }

  // Expose for language switching
  window.i18n = {
    load: load,
    apply: apply,
    t: window.t,
    lang: function(){ return _lang; }
  };

  // Auto-load on DOM ready
  if(document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", function(){ load(); });
  } else {
    load();
  }
})();
