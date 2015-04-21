/*jshint browser:true, camelcase: false*/
/*globals $, Facetly*/
$(window).load(function () {
    Facetly.init({
        selector: '#facetly',
        elasticsearch: window.location.protocol + '//' + window.location.host + ':9200' + '/legisletters/_search',
        onSerialize: function(/*obj, str*/) {
            // console.debug(str);
        },
        excludedFields: [
            "url",
            "identifier",
            "scrapeTime",
            "html"
        ],
        facets: {
            text: {
                terms: {
                    field: "text",
                    size: 0
                }
            },
            letterDate: {
                date_histogram : {
                    field : "letterDate",
                    interval : "month"
                }
            },
            recipients: {
                terms: {
                    field: "recipients",
                    size: 0
                }
            },
            signatures: {
                terms: {
                    field: "signatures",
                    size: 0
                }
            }
            /*
            name: {
                terms: {
                    field: "name"
                }
            },
            group: {
                terms: {
                    field: "groups.name",
                },
                nested: "groups"  
            },
            city: {
                terms: {
                    field: "addresses.city"
                },
                nested: "addresses"
            },
            country: {
                terms: {
                    field: "addresses.country"
                },
                nested: "addresses"
            },
            createdAt: {
                date_histogram : {
                    field : "createdAt",
                    interval : "day"
                }
            }
            */
        }
    });
});
