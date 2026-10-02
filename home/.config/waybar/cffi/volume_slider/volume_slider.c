#include "waybar_cffi_module.h"

#include <math.h>
#include <pulse/glib-mainloop.h>
#include <pulse/pulseaudio.h>
#include <stdlib.h>
#include <string.h>

#define NORMAL_MAX 100.0
#define BOOST_MAX 150.0
#define NORMAL_WIDTH 85
#define BOOST_WIDTH 128
#define ANIMATION_STEPS 12
#define BOOST_STATE_PATH "__DOTFILES_HOME__/.config/waybar/audio-boost"

typedef struct {
  GtkWidget* box;
  GtkWidget* scale;
  pa_glib_mainloop* pulse_loop;
  pa_context* pulse_context;
  GFile* boost_state_file;
  GFileMonitor* boost_state_monitor;
  char* sink_name;
  pa_cvolume sink_volume;
  gboolean internal_update;
  gboolean expanded;
  guint animation_id;
  int animation_step;
  int animation_from;
  int animation_to;
} VolumeSlider;

const size_t wbcffi_version = 2;

static void refresh_default_sink(VolumeSlider* instance);

static void update_overdrive_style(VolumeSlider* instance, double percent) {
  GtkStyleContext* style = gtk_widget_get_style_context(instance->scale);
  if (percent > NORMAL_MAX) {
    gtk_style_context_add_class(style, "over-100");
  } else {
    gtk_style_context_remove_class(style, "over-100");
  }
}

static void operation_done(pa_context* context, int success, void* userdata) {
  (void)context;
  (void)success;
  (void)userdata;
}

static void set_sink_percent(VolumeSlider* instance, double percent) {
  if (instance->pulse_context == NULL || instance->sink_name == NULL ||
      pa_context_get_state(instance->pulse_context) != PA_CONTEXT_READY ||
      instance->sink_volume.channels == 0) {
    return;
  }

  pa_volume_t target = (pa_volume_t)llround(
      percent * (double)PA_VOLUME_NORM / 100.0);
  pa_cvolume volume = instance->sink_volume;
  pa_cvolume_scale(&volume, target);

  pa_operation* operation = pa_context_set_sink_volume_by_name(
      instance->pulse_context, instance->sink_name, &volume,
      operation_done, instance);
  if (operation != NULL) {
    pa_operation_unref(operation);
  }
  operation = pa_context_set_sink_mute_by_name(
      instance->pulse_context, instance->sink_name, 0,
      operation_done, instance);
  if (operation != NULL) {
    pa_operation_unref(operation);
  }
}

static void on_scale_changed(GtkRange* range, gpointer userdata) {
  VolumeSlider* instance = userdata;
  double percent = gtk_range_get_value(range);
  update_overdrive_style(instance, percent);
  if (instance->internal_update) {
    return;
  }
  set_sink_percent(instance, percent);
}

static gboolean animate_width(gpointer userdata) {
  VolumeSlider* instance = userdata;
  instance->animation_step++;
  double progress = (double)instance->animation_step / ANIMATION_STEPS;
  /* Smoothstep keeps the ends of the transition soft. */
  progress = progress * progress * (3.0 - 2.0 * progress);
  int width = (int)lround(
      instance->animation_from +
      (instance->animation_to - instance->animation_from) * progress);
  gtk_widget_set_size_request(instance->scale, width, -1);

  if (instance->animation_step < ANIMATION_STEPS) {
    return G_SOURCE_CONTINUE;
  }

  instance->animation_id = 0;
  if (!instance->expanded) {
    gtk_range_set_range(GTK_RANGE(instance->scale), 0.0, NORMAL_MAX);
    gtk_style_context_remove_class(
        gtk_widget_get_style_context(instance->scale), "boost");
    gtk_style_context_remove_class(
        gtk_widget_get_style_context(instance->box), "expanded");
  }
  return G_SOURCE_REMOVE;
}

static void start_width_animation(VolumeSlider* instance, int target) {
  if (instance->animation_id != 0) {
    g_source_remove(instance->animation_id);
    instance->animation_id = 0;
  }
  int current = -1;
  gtk_widget_get_size_request(instance->scale, &current, NULL);
  if (current < 0) {
    current = instance->expanded ? NORMAL_WIDTH : BOOST_WIDTH;
  }
  instance->animation_from = current;
  instance->animation_to = target;
  instance->animation_step = 0;
  instance->animation_id = g_timeout_add(15, animate_width, instance);
}

static void set_boost_mode(VolumeSlider* instance, gboolean enabled) {
  if (instance->expanded == enabled) {
    return;
  }
  instance->expanded = enabled;

  if (enabled) {
    gtk_range_set_range(GTK_RANGE(instance->scale), 0.0, BOOST_MAX);
    gtk_style_context_add_class(
        gtk_widget_get_style_context(instance->scale), "boost");
    gtk_style_context_add_class(
        gtk_widget_get_style_context(instance->box), "expanded");
    start_width_animation(instance, BOOST_WIDTH);
  } else {
    double current = gtk_range_get_value(GTK_RANGE(instance->scale));
    if (current > NORMAL_MAX) {
      instance->internal_update = TRUE;
      gtk_range_set_value(GTK_RANGE(instance->scale), NORMAL_MAX);
      instance->internal_update = FALSE;
      set_sink_percent(instance, NORMAL_MAX);
    }
    start_width_animation(instance, NORMAL_WIDTH);
  }
}

static gboolean boost_state_enabled(void) {
  gchar* contents = NULL;
  gsize length = 0;
  gboolean enabled = FALSE;
  if (g_file_get_contents(BOOST_STATE_PATH, &contents, &length, NULL)) {
    enabled = length > 0 && contents[0] == '1';
  }
  g_free(contents);
  return enabled;
}

static void sync_boost_state(VolumeSlider* instance) {
  set_boost_mode(instance, boost_state_enabled());
}

static void on_boost_state_changed(GFileMonitor* monitor, GFile* file,
                                   GFile* other_file,
                                   GFileMonitorEvent event_type,
                                   gpointer userdata) {
  (void)monitor;
  (void)file;
  (void)other_file;
  if (event_type == G_FILE_MONITOR_EVENT_CHANGED ||
      event_type == G_FILE_MONITOR_EVENT_CHANGES_DONE_HINT ||
      event_type == G_FILE_MONITOR_EVENT_CREATED) {
    sync_boost_state(userdata);
  }
}

static void sink_info_callback(pa_context* context, const pa_sink_info* info,
                               int end_of_list, void* userdata) {
  (void)context;
  VolumeSlider* instance = userdata;
  if (end_of_list || info == NULL) {
    return;
  }

  instance->sink_volume = info->volume;
  double percent = 100.0 * pa_cvolume_avg(&info->volume) /
                   (double)PA_VOLUME_NORM;
  instance->internal_update = TRUE;
  gtk_range_set_value(GTK_RANGE(instance->scale), percent);
  instance->internal_update = FALSE;
  update_overdrive_style(instance, percent);
}

static void server_info_callback(pa_context* context,
                                 const pa_server_info* info,
                                 void* userdata) {
  VolumeSlider* instance = userdata;
  if (info == NULL || info->default_sink_name == NULL) {
    return;
  }
  g_free(instance->sink_name);
  instance->sink_name = g_strdup(info->default_sink_name);
  pa_operation* operation = pa_context_get_sink_info_by_name(
      context, instance->sink_name, sink_info_callback, instance);
  if (operation != NULL) {
    pa_operation_unref(operation);
  }
}

static void refresh_default_sink(VolumeSlider* instance) {
  if (instance->pulse_context == NULL ||
      pa_context_get_state(instance->pulse_context) != PA_CONTEXT_READY) {
    return;
  }
  pa_operation* operation = pa_context_get_server_info(
      instance->pulse_context, server_info_callback, instance);
  if (operation != NULL) {
    pa_operation_unref(operation);
  }
}

static void subscription_callback(pa_context* context,
                                  pa_subscription_event_type_t event,
                                  uint32_t index, void* userdata) {
  (void)context;
  (void)index;
  VolumeSlider* instance = userdata;
  pa_subscription_event_type_t facility =
      event & PA_SUBSCRIPTION_EVENT_FACILITY_MASK;
  if (facility == PA_SUBSCRIPTION_EVENT_SINK ||
      facility == PA_SUBSCRIPTION_EVENT_SERVER) {
    refresh_default_sink(instance);
  }
}

static void context_state_callback(pa_context* context, void* userdata) {
  VolumeSlider* instance = userdata;
  if (pa_context_get_state(context) != PA_CONTEXT_READY) {
    return;
  }
  pa_context_set_subscribe_callback(
      context, subscription_callback, instance);
  pa_operation* operation = pa_context_subscribe(
      context, PA_SUBSCRIPTION_MASK_SINK | PA_SUBSCRIPTION_MASK_SERVER,
      operation_done, instance);
  if (operation != NULL) {
    pa_operation_unref(operation);
  }
  refresh_default_sink(instance);
}

void* wbcffi_init(const wbcffi_init_info* init_info,
                  const wbcffi_config_entry* config_entries,
                  size_t config_entries_len) {
  (void)config_entries;
  (void)config_entries_len;

  VolumeSlider* instance = g_new0(VolumeSlider, 1);
  GtkContainer* root = init_info->get_root_widget(init_info->obj);

  instance->box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
  gtk_widget_set_name(instance->box, "volume-slider-module");
  gtk_container_add(root, instance->box);

  instance->scale = gtk_scale_new_with_range(
      GTK_ORIENTATION_HORIZONTAL, 0.0, NORMAL_MAX, 1.0);
  gtk_widget_set_name(instance->scale, "volume-slider");
  gtk_scale_set_draw_value(GTK_SCALE(instance->scale), FALSE);
  gtk_range_set_increments(GTK_RANGE(instance->scale), 1.0, 5.0);
  gtk_widget_set_size_request(instance->scale, NORMAL_WIDTH, -1);
  gtk_box_pack_start(GTK_BOX(instance->box), instance->scale, FALSE, FALSE, 0);
  g_signal_connect(instance->scale, "value-changed",
                   G_CALLBACK(on_scale_changed), instance);

  instance->boost_state_file = g_file_new_for_path(BOOST_STATE_PATH);
  instance->boost_state_monitor = g_file_monitor_file(
      instance->boost_state_file, G_FILE_MONITOR_NONE, NULL, NULL);
  if (instance->boost_state_monitor != NULL) {
    g_signal_connect(instance->boost_state_monitor, "changed",
                     G_CALLBACK(on_boost_state_changed), instance);
  }
  sync_boost_state(instance);

  instance->pulse_loop = pa_glib_mainloop_new(g_main_context_default());
  if (instance->pulse_loop == NULL) {
    wbcffi_deinit(instance);
    return NULL;
  }
  instance->pulse_context = pa_context_new(
      pa_glib_mainloop_get_api(instance->pulse_loop), "Waybar volume slider");
  if (instance->pulse_context == NULL) {
    wbcffi_deinit(instance);
    return NULL;
  }
  pa_context_set_state_callback(
      instance->pulse_context, context_state_callback, instance);
  if (pa_context_connect(instance->pulse_context, NULL,
                         PA_CONTEXT_NOFLAGS, NULL) < 0) {
    wbcffi_deinit(instance);
    return NULL;
  }

  return instance;
}

void wbcffi_deinit(void* data) {
  VolumeSlider* instance = data;
  if (instance == NULL) {
    return;
  }
  if (instance->animation_id != 0) {
    g_source_remove(instance->animation_id);
  }
  if (instance->pulse_context != NULL) {
    pa_context_set_state_callback(instance->pulse_context, NULL, NULL);
    pa_context_set_subscribe_callback(instance->pulse_context, NULL, NULL);
    pa_context_disconnect(instance->pulse_context);
    pa_context_unref(instance->pulse_context);
  }
  if (instance->pulse_loop != NULL) {
    pa_glib_mainloop_free(instance->pulse_loop);
  }
  if (instance->boost_state_monitor != NULL) {
    g_file_monitor_cancel(instance->boost_state_monitor);
    g_object_unref(instance->boost_state_monitor);
  }
  if (instance->boost_state_file != NULL) {
    g_object_unref(instance->boost_state_file);
  }
  g_free(instance->sink_name);
  g_free(instance);
}

void wbcffi_update(void* instance, const char* action_name) {
  (void)instance;
  (void)action_name;
}

void wbcffi_refresh(void* instance, int signal) {
  (void)signal;
  refresh_default_sink(instance);
}

void wbcffi_doaction(void* instance, const char* action_name) {
  (void)instance;
  (void)action_name;
}
