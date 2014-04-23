CloudPebble.Locations = (function() {
    var slugs = {};

    var activate_current = function() {
        var location = get_location();

        if(slugs[location]) {
            slugs[location]();
        }
    };

    var get_location = function() {
        var location = window.location.hash;

        return location.substr(1);
    };

    var set_location = function(slug) {
        if(slug == get_location()) return;

        window.location.hash = slug;
    };

    return {
        Init: function() {
            activate_current();

            $(window).on('hashchange', function() {
                activate_current();
            });
        },
        Add: function(slug, func) {
            if(get_location() == slug) {
                func();
            }

            slugs[slug] = func;
        },
        Set: function(slug) {
            set_location(slug);
        }
    }
})()