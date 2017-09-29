// Modules
var gulp        = require('gulp');
var favicon     = require('gulp-real-favicon');
var fs          = require('fs');
var runSequence = require('run-sequence'); // Using until gulp v4 is released
var watch       = require('gulp-watch');
var batch       = require('gulp-batch');
var reload      = require('gulp-livereload');
var sync        = require('gulp-sync')(gulp).sync;
var child       = require('child_process');
var util        = require('gulp-util');
var path        = require('path');
var os          = require('os');

// Enviroment variables
var folderAsset = 'kqueen/asset';
var folderTemplate = 'kqueen/templates';
var bootstrapDir = './node_modules/bootstrap-sass';

// Other variables
var faviconData = folderAsset + '/dynamic/favicon/data.json';

// Application server
var server = null;

// SASS Task
gulp.task('sass', function() {
	var sass = require('gulp-sass');
	var ext = require('gulp-ext-replace');
	return gulp.src(folderAsset + '/dynamic/scss/main.scss')
        .pipe(sass({
            includePaths: [bootstrapDir + '/assets/stylesheets'],
            outputStyle: 'compressed',
        }))
        .pipe(ext('.min.css'))
        .pipe(gulp.dest(folderAsset + '/static/css/'))
        .pipe(reload());
});

// JavaScript Task
gulp.task('javascript', function() {
	var concat = require('gulp-concat');
	var minify = require('gulp-minify');
	var babel = require('gulp-babel');
	return gulp.src(folderAsset + '/dynamic/js/*.js')
		.pipe(babel({
			presets: ['es2015']
		}))
		.pipe(concat('all.js'))
		.pipe(minify({
			ext:{
				src:'.js',
				min:'.min.js'
			}
		}))
		.pipe(gulp.dest(folderAsset + '/static/js/'))
		.pipe(reload());
});

// jQuery Task
gulp.task('jquery', function() {
	return gulp.src('node_modules/jquery/dist/jquery.min.*')
		.pipe(gulp.dest(folderAsset + '/static/js/'));
});

// Underscore Task
gulp.task('underscore', function() {
	return gulp.src('node_modules/underscore/underscore-min.*')
		.pipe(gulp.dest(folderAsset + '/static/js/'));
});

// All JS
gulp.task('javascript-all', ['javascript', 'jquery', 'underscore']);

// Fonts Task
gulp.task('fonts', function() {
    return gulp.src(bootstrapDir + '/assets/fonts/**/*')
        .pipe(gulp.dest(folderAsset + '/static/fonts/'));
});

// Favicon Generation and Injection Task
gulp.task('favicon', function() {
	runSequence('favicon-generate', 'favicon-inject');
});

// Generate the icons. This task takes a few seconds to complete.
// You should run it at least once to create the icons. Then,
// you should run it whenever RealFaviconGenerator updates its
// package (see the favicon-update task below).
gulp.task('favicon-generate', function(done) {
	var favColor = '#525252';
	favicon.generateFavicon({
		masterPicture: folderAsset + '/dynamic/favicon/logo.png',
		dest: folderAsset + '/static/favicon/',
		iconsPath: '/static/favicon/',
		design: {
			ios: {
				pictureAspect: 'backgroundAndMargin',
				backgroundColor: favColor,
				margin: '14%'
			},
			desktopBrowser: {},
			windows: {
				pictureAspect: 'noChange',
				backgroundColor: favColor,
				onConflict: 'override'
			},
			androidChrome: {
				pictureAspect: 'noChange',
				themeColor: favColor,
				manifest: {
					name: 'Blueprint',
					display: 'browser',
					orientation: 'notSet',
					onConflict: 'override',
					declared: true
				}
			},
			safariPinnedTab: {
				pictureAspect: 'silhouette',
				themeColor: favColor
			}
		},
		settings: {
			scalingAlgorithm: 'Mitchell',
			errorOnImageTooSmall: false
		},
		versioning: {
			paramName: 'v1.0',
			paramValue: '3eepn6WlLO'
		},
		markupFile: faviconData
	}, function() {
		done();
	});
});

// Inject the favicon markups in your HTML pages. You should run
// this task whenever you modify a page. You can keep this task
// as is or refactor your existing HTML pipeline.
gulp.task('favicon-inject', function() {
	return gulp.src([folderTemplate + '/partial/favicon.tmpl'])
		.pipe(favicon.injectFaviconMarkups(JSON.parse(fs.readFileSync(faviconData)).favicon.html_code))
		.pipe(gulp.dest(folderTemplate + '/partial/'));
});

// Check for updates on RealFaviconGenerator (think: Apple has just
// released a new Touch icon along with the latest version of iOS).
// Run this task from time to time. Ideally, make it part of your
// continuous integration system.
gulp.task('favicon-update', function(done) {
	var currentVersion = JSON.parse(fs.readFileSync(faviconData)).version;
	return favicon.checkForUpdates(currentVersion, function(err) {
		if (err) {
			throw err;
		}
	});
});

// Monitor files for changes
gulp.task('watch', ['build'], function () {
    watch('./kqueen/asset/dynamic/**/*.scss', batch(function (events, done) {
        gulp.start('sass', done);
    }));
    watch('./kqueen/asset/dynamic/**/*.js', batch(function (events, done) {
        gulp.start('javascript-all', done);
    }));
});

// Init - every task
gulp.task('build', ['sass', 'javascript-all', 'favicon']);

// Default - only run the tasks that change often
gulp.task('default', ['build']);
