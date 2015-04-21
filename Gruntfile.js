/*jshint node: true, camelcase: false*/
/*globals module: true*/

module.exports = function(grunt) {
  grunt.initConfig({
    bower_concat: {
      all: {
        dest: 'dist/js/bower_deps.js',
        dependencies: {
          "backbone": ["underscore", "jquery"],
          "bootstrap-slider": ["bootstrap"],
          "jquery-ui": ["jquery"],
          "bootstrap": ["jquery-ui"],
          "visualsearch": ["backbone", "underscore"]
        },
        cssDest: 'dist/css/bower_deps.css',
        exclude: [
          "jQuery"
        ]
      }
    },
    concat: {
      all: {
        files: {
          'dist/js/legisletters.js': [
            'src/js/*'
          ],
          'dist/css/bower_deps.css': [
            'dist/css/bower_deps.css',
            'bower_components/jquery-ui/themes/base/jquery-ui.css',
            'bower_components/visualsearch/build-min/visualsearch-datauri.css'
          ]
        }
      }
    },
    copy: {
      all: {
        cwd: 'src',
        src: ['css/*', 'index.html'],
        dest: 'dist',
        expand: true
      },
      bootstrap: {
        cwd: 'bower_components/bootstrap/',
        src: ['img/*'],
        dest: 'dist',
        expand: true
      }
    },
    watch: {
      all: {
        files: 'src/**',
        tasks: 'default'
      }
    }
  });
  grunt.loadNpmTasks('grunt-bower-concat');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-watch');

  grunt.registerTask('default', ['bower_concat', 'copy', 'concat']);
};
