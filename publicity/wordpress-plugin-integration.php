<?php
/*
Plugin Name: MyHRDC Show Posts
Plugin URI: https://my.hrdctheater.org/
Description: Pull publicity info from MyHRDC to display on the website
Version: 1.0.0
Author: Aaron Olkin
License: GPLv2 or later
*/

function makePost($show) {
  $post_id = 0 - $show->show_id; // negative ID, to avoid clash with a valid post
  $post = new stdClass();
  $post->ID = $post_id;
  $post->post_author = 1;
  $post->post_date = current_time( 'mysql' );
  $post->post_date_gmt = current_time( 'mysql', 1 );
  $post->post_title = $show->title;
  $post->post_content = $show->body;
  $post->post_excerpt =  "<b>" . $show->season . " " . $show->year . "</b><br>" . $show->blurb;
  $post->post_category = 'shows';
  $post->post_status = 'publish';
  $post->comment_status = 'closed';
  $post->ping_status = 'closed';
  $post->post_name = $show->slug;
  $post->post_type = 'post';
  $post->filter = 'raw'; // important!

  $wp_post = new WP_Post($post);
  wp_cache_add($post_id, $wp_post, 'posts');
  wp_cache_add($post_id, array(4), 'category_relationships');
  return $wp_post;
}

function fetch( $query ) {
  $response = wp_remote_get("https://my.hrdctheater.org/publicity/api" . $query);
  if (is_wp_error($response)) {
    return false;
  }
  $body = wp_remote_retrieve_body($response);
  return json_decode($body);
}

function updateQuerySingle( $wp_post ) {
  global $wp, $wp_query;

  // Update the main query
  $wp_query->post = $wp_post;
  $wp_query->posts = array( $wp_post );
  $wp_query->queried_object = $wp_post;
  $wp_query->queried_object_id = $wp_post->ID;
  $wp_query->found_posts = 1;
  $wp_query->post_count = 1;
  $wp_query->max_num_pages = 1;
  $wp_query->is_page = true;
  $wp_query->is_singular = true;
  $wp_query->is_single = true;
  $wp_query->is_attachment = false;
  $wp_query->is_archive = false;
  $wp_query->is_category = false;
  $wp_query->is_tag = false;
  $wp_query->is_tax = false;
  $wp_query->is_author = false;
  $wp_query->is_date = false;
  $wp_query->is_year = false;
  $wp_query->is_month = false;
  $wp_query->is_day = false;
  $wp_query->is_time = false;
  $wp_query->is_search = false;
  $wp_query->is_feed = false;
  $wp_query->is_comment_feed = false;
  $wp_query->is_trackback = false;
  $wp_query->is_home = false;
  $wp_query->is_embed = false;
  $wp_query->is_404 = false;
  $wp_query->is_paged = false;
  $wp_query->is_admin = false;
  $wp_query->is_preview = false;
  $wp_query->is_robots = false;
  $wp_query->is_posts_page = false;
  $wp_query->is_post_type_archive = false;

  // Update globals
  $GLOBALS['wp_query'] = $wp_query;
  $wp->register_globals();
}

function updateQueryMulti( $wp_posts, $meta ) {
  global $wp, $wp_query;

  // Update the main query
  $wp_query->posts = $wp_posts;
  $wp_query->found_posts = $meta->count;
  $wp_query->post_count = count($wp_posts);
  $wp_query->max_num_pages = $meta->pages;
  $wp_query->is_page = false;
  $wp_query->is_singular = false;
  $wp_query->is_single = false;
  $wp_query->is_attachment = false;
  $wp_query->is_archive = true;
  $wp_query->is_category = true;
  $wp_query->is_tag = false;
  $wp_query->is_tax = false;
  $wp_query->is_author = false;
  $wp_query->is_date = false;
  $wp_query->is_year = false;
  $wp_query->is_month = false;
  $wp_query->is_day = false;
  $wp_query->is_time = false;
  $wp_query->is_search = false;
  $wp_query->is_feed = false;
  $wp_query->is_comment_feed = false;
  $wp_query->is_trackback = false;
  $wp_query->is_home = false;
  $wp_query->is_embed = false;
  $wp_query->is_404 = false;
  $wp_query->is_paged = true;
  $wp_query->is_admin = false;
  $wp_query->is_preview = false;
  $wp_query->is_robots = false;
  $wp_query->is_posts_page = true;
  $wp_query->is_post_type_archive = false;

  // Update globals
  $GLOBALS['wp_query'] = $wp_query;
  $wp->register_globals();
}

function updateQuerySearch( $wp_posts, $meta ) {
  global $wp, $wp_query;

  // Update the main query
  $wp_query->posts = $wp_posts + $wp_query->posts;
  $wp_query->found_posts = $meta->count + $wp_query->found_posts;
  $wp_query->post_count = count($wp_posts) + $wp_query->post_count;

  // Update globals
  $GLOBALS['wp_query'] = $wp_query;
  $wp->register_globals();
}

add_action( 'template_redirect', 'spoof_main_query', 1);
function spoof_main_query() {
  $request_path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
  if (is_search()) {
    $shows = fetch("/query?title=" . get_search_query());
    if ($shows->count > 0) {
      $posts = array_map("makePost", $shows->shows);
      updateQuerySearch($posts, $shows);
    }
  } else if (str_starts_with($request_path, '/shows/')) {
    $slug = substr($request_path, 7);
    if (empty($slug)) {
      $shows = fetch("/query?" . parse_url($_SERVER['REQUEST_URI'], PHP_URL_QUERY));
      $posts = array_map("makePost", $shows->shows);
      updateQueryMulti($posts, $shows);
    } else {
      if (str_ends_with($slug, '/')) {
	$slug = substr($slug, 0, -1);
      }
      $show = fetch("/slug/" . $slug);
      if ($show != false) {
	$wp_post = makePost($show);
	updateQuerySingle($wp_post);
      }
    }
   }
}

?>
