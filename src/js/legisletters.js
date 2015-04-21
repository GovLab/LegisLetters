/*jshint browser:true, camelcase: false*/
/*globals $, Facetly*/
$(window).load(function () {
    Facetly.init({
        selector: '#facetly',
        elasticsearch: 'http://localhost:9200/_all/_search',
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
                    size: 10
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
                    size: 10
                }
            },
            signatures: {
                terms: {
                    field: "signatures",
                    size: 10
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
