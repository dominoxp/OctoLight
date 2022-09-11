# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import time

import octoprint.plugin
from octoprint.events import Events
import flask

import math
import subprocess
from octoprint.util import RepeatedTimer


class OctoLightPlugin(
	octoprint.plugin.AssetPlugin,
	octoprint.plugin.StartupPlugin,
	octoprint.plugin.TemplatePlugin,
	octoprint.plugin.SimpleApiPlugin,
	octoprint.plugin.SettingsPlugin,
	octoprint.plugin.EventHandlerPlugin,
	octoprint.plugin.RestartNeedingPlugin
):
	event_options = [
		{"name": "Nothing", "value": "na"},
		{"name": "Turn Light On", "value": "on"},
		{"name": "Turn Light Off", "value": "off"},
		{"name": "Delay Turn Light Off", "value": "delay"}
	]
	monitored_events = [
		{"label": "Printer Start:", "settingName": "event_printer_start"},
		{"label": "Printer Done:", "settingName": "event_printer_done"},
		{"label": "Printer Failed:", "settingName": "event_printer_failed"},
		{"label": "Printer Cancelled:", "settingName": "event_printer_cancelled"},
		{"label": "Printer Paused:", "settingName": "event_printer_paused"},
		{"label": "Printer Error:", "settingName": "event_printer_error"}
	]

	light_state = False
	delayed_state = None

	def get_settings_defaults(self):
		return dict(
			on_command="",
			off_command="",
			status_command="",
			inverted_output=False,
			delay_off=5,

			# Setup the default value for each event
			event_printer_start=self.event_options[0]["value"],
			event_printer_done=self.event_options[0]["value"],
			event_printer_failed=self.event_options[0]["value"],
			event_printer_cancelled=self.event_options[0]["value"],
			event_printer_paused=self.event_options[0]["value"],
			event_printer_error=self.event_options[0]["value"]
		)

	def get_template_configs(self):
		return [
			dict(type="navbar", custom_bindings=True),
			dict(type="settings", custom_bindings=True)
		]

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/octolight.js"],
			css=["css/octolight.css"],
			# less=["less/octolight.less"]
		)

	def get_template_vars(self):
		return {
			"event_options": self.event_options,
			"monitored_events": self.monitored_events
		}

	def on_after_startup(self):
		self._logger.info("--------------------------------------------")
		self._logger.info("OctoLight started, listening for GET request")
		self._logger.info("Light on: '{}', Light off: '{}', Light status: '{}', Delay Time: {}".format(
			self._settings.get(["on_command"]),
			self._settings.get(["off_command"]),
			self._settings.get(["status_command"]),
			self._settings.get(["delay_off"])
		))
		self._logger.info("--------------------------------------------")

		# Get current light statue of command
		light_state = self.get_light_state()

		self._logger.info("After Startup. Light state: {}".format(light_state))

		self._plugin_manager.send_plugin_message(self._identifier, dict(isLightOn=light_state))

	def light_toggle(self):
		self.stopTimer()

		# Turn light off if already on
		current_state = self.get_light_state()
		self.change_light_state(not current_state)

		self._logger.info("Got request. Light state: {}".format(not current_state))

		self._plugin_manager.send_plugin_message(self._identifier, dict(isLightOn=not current_state))

	def on_api_get(self, request):
		action = request.args.get('action', default="toggle", type=str)
		delay = request.args.get('delay', default=self._settings.get(["delay_off"]), type=int)

		if action == "toggle":
			self.light_toggle()
			return flask.jsonify(state=self.get_light_state())

		elif action == "getState":
			return flask.jsonify(state=self.get_light_state())

		elif action == "turnOn":
			self.change_light_state(True)
			return flask.jsonify(state=self.get_light_state())

		elif action == "turnOff":
			self.change_light_state(False)
			return flask.jsonify(state=self.get_light_state())

		# Turn on light and setup timer
		elif action == "delayOff":
			self.delayed_off_setup(delay)
			return flask.jsonify(state=self.get_light_state())

		# Turn off off timer and light
		elif action == "delayOffStop":
			self.delayed_off()
			return flask.jsonify(state=self.get_light_state())

		else:
			return flask.jsonify(error="action not recognized")

	# This stops the current timer, this does not control the light
	def stopTimer(self):
		if self.delayed_state is not None:
			self._logger.info("Stopping schedule")
			self.delayed_state.cancel()
			self.delayed_state = None

	# This sets up the timer, this does not control the light
	# Check if the timer is already running, if so, stop it, then set it up with a new time
	def startTimer(self, mins):
		if math.isnan(int(mins)):
			self._logger.info("Error: Received value that is not an int: {}".format(
				mins
			))
			return

		self.stopTimer()

		self._logger.info("Setting up schedule")
		self.delayed_state = RepeatedTimer(int(mins) * 60, self.delayed_off)
		self.delayed_state.start()
		self._logger.info("Time till shutoff: {} seconds".format(
			int(mins) * 60
		))

	# Setup the light to shutoff when called
	def delayed_off(self):
		self.change_light_state(False)

	# Setup the light to turn on then off after a set time
	def delayed_off_setup(self, mins):
		# Make sure a value was sent
		if math.isnan(int(mins)):
			self._logger.info("Error: Received value that is not an int: {}".format(
				mins
			))
			return

		# Stop any past timers
		self.delayed_off()

		self.change_light_state(True)
		self.startTimer(mins)

	def on_event(self, event, payload):
		if event == Events.CLIENT_OPENED:
			self._plugin_manager.send_plugin_message(self._identifier, dict(isLightOn=self.get_light_state()))
			return
		if event == Events.PRINT_STARTED:
			self.trigger_event(self._settings.get(["event_printer_start"])[0])
			return
		if event == Events.PRINT_DONE:
			self.trigger_event(self._settings.get(["event_printer_done"])[0])
			return
		if event == Events.PRINT_FAILED:
			self.trigger_event(self._settings.get(["event_printer_failed"])[0])
			return
		if event == Events.PRINT_CANCELLED:
			self.trigger_event(self._settings.get(["event_printer_cancelled"])[0])
			return
		if event == Events.PRINT_PAUSED:
			self.trigger_event(self._settings.get(["event_printer_paused"])[0])
			return
		if event == Events.ERROR:
			self.trigger_event(self._settings.get(["event_printer_error"])[0])
			return

	# Handles the event that should happen
	def trigger_event(self, user_setting):
		if user_setting == "on":
			self.change_light_state(True)
		elif user_setting == "off":
			self.change_light_state(False)
		elif user_setting == "delay":
			self.delayed_off_setup(self._settings.get(["delay_off"]))
		else:
			self._logger.info("Unknown event trigger, received: {}".format(
				user_setting
			))

		return

	def get_update_information(self):
		return dict(
			octolight=dict(
				displayName="OctoLight",
				displayVersion=self._plugin_version,

				type="github_release",
				current=self._plugin_version,

				user="dominoxp",
				repo="OctoLight",
				pip="https://github.com/dominoxp/OctoLight/archive/{target}.zip"
			)
		)

	def get_light_state(self):
		# Get current light statue of command
		p = subprocess.Popen(self._settings.get(["status_command"]), shell=True)

		for _ in range(600):
			if p.poll() is None:
				time.sleep(0.1)
			else:
				break

		return p.returncode == 0

	def change_light_state(self, value):
		# Set current light statue of command
		if value:
			p = subprocess.Popen(self._settings.get(["on_command"]), shell=True)
		else:
			self.stopTimer()
			p = subprocess.Popen(self._settings.get(["off_command"]), shell=True)

		for _ in range(600):
			if p.poll() is None:
				time.sleep(0.1)
			else:
				break

		return p.returncode == 0


__plugin_pythoncompat__ = ">=2.7,<4"
__plugin_implementation__ = OctoLightPlugin()

__plugin_hooks__ = {
	"octoprint.plugin.softwareupdate.check_config":
		__plugin_implementation__.get_update_information
}
