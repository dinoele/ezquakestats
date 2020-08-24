#!/usr/bin/python
import pdb
import time, sys
from datetime import timedelta, date, datetime
import time
import re
from operator import itemgetter, attrgetter, methodcaller

from optparse import OptionParser,OptionValueError

import fileinput
import os.path

import HTML

def enum(**enums):
    return type('Enum', (), enums)

possibleWeapons = ["lg", "gl", "rl", "sg", "ssg", "ng", "sng", "axe", "tele", "other"]

HtmlColor = enum( COLOR_RED  ="#ff3333",
                  COLOR_GREEN="#009900",
                  COLOR_GRAY ="#8c8c8c",
                  COLOR_GOLD ="#e6c300",
                  COLOR_BLUE ="#0000cc",
                  COLOR_PURPLE = "#6600cc",
                  COLOR_ORANGE = "#ff8000",
                  COLOR_CYAN = "#00cccc",
                  COLOR_MAGENTA = "#cc00cc" )

possibleColors = [HtmlColor.COLOR_RED,
                  HtmlColor.COLOR_GREEN,
                  HtmlColor.COLOR_GOLD,
                  HtmlColor.COLOR_BLUE,
                  HtmlColor.COLOR_PURPLE,
                  HtmlColor.COLOR_ORANGE,
                  HtmlColor.COLOR_CYAN,
                  HtmlColor.COLOR_MAGENTA]

CURRENT_VERSION = "1.25"
                  
LOG_TIMESTAMP_DELIMITER = " <-> "

DEFAULT_PLAYER_NAME_MAX_LEN = 10

NEW_FILE_TIME_DETECTION = 60*60*4 # 4 hours

READ_LINES_LIMIT = 10000
LOGS_INDEX_FILE_NAME = "logs.html"
TEAM_LOGS_INDEX_FILE_NAME = "teamlogs.html"
LOGS_BY_MAP_FILE_NAME = "logs_by_maps.html"
TOURNAMENT_TABLE_FILE_NAME = "ezquakestats/tournament_table.html"
TOTALS_FILE_NAME = "totals.html"
ALLPLAYERS_FILE_NAME = "allplayers.html"
REPORTS_FOLDER = "../";

NEW_GIF_TAG = "<img src=\"new2.gif\" alt=\"New\" style=\"width:48px;height:36px;\">";

ERROR_LOG_FILE_NAME = "errors"
SKIPED_LINES_FILE_NAME = "skiped_lines"

HTML_CURRENT_VERSION = "<!-- CURRENT_VERSION: " + CURRENT_VERSION + " -->\n"

HTML_HEADER_STR = "<!DOCTYPE html>\n<html>\n<head>\n<link rel=\"icon\" type=\"image/png\" href=\"ezquakestats/img/quake-icon.png\"/>\n" + HTML_CURRENT_VERSION + "</head>\n<body>\n<pre>"
HTML_FOOTER_STR = "</pre>\n</body>\n</html>"

HTML_HEADER_SCRIPT_SECTION = \
    "<!DOCTYPE html>\n<html>\n<head>\n" \
    "HTML_CURRENT_VERSION_PLACE" \
    "<title>PAGE_TITLE</title>\n" \
    "<link rel=\"icon\" type=\"image/png\" href=\"ezquakestats/img/quake-icon.png\" />" \
    "<script type=\"text/javascript\" src=\"https://ajax.googleapis.com/ajax/libs/jquery/1.4.4/jquery.min.js\"></script>\n" \
    "<script type=\"text/javascript\" src=\"https://www.gstatic.com/charts/loader.js\"></script>\n" \
    "<style>\n" \
    ".tooltip {position:absolute;z-index:1070;display:block;font-size:12px;line-height:1.4;visibility:visible;filter:alpha(opacity=0);opacity:0}\n" \
    ".tooltip.in{filter:alpha(opacity=90);opacity:.9}\n" \
    ".tooltip.top{padding:5px 0;margin-top:-3px}.\n" \
    "tooltip.right{padding:0 5px;margin-left:3px}\n" \
    ".tooltip.bottom{padding:5px 0;margin-top:3px}\n" \
    ".tooltip.left{padding:0 5px;margin-left:-3px}\n" \
    ".tooltip-inner{max-width:200px;padding:3px 8px;color:#fff;text-align:center;text-decoration:none;background-color:#000;border-radius:4px}\n" \
    ".tooltip-arrow{position:absolute;width:0;height:0;border-color:transparent;border-style:solid}\n" \
    ".tooltip.top \n" \
    ".tooltip-arrow{bottom:0;left:50%;margin-left:-5px;border-width:5px 5px 0;border-top-color:#000}\n" \
    ".tooltip.top-left \n" \
    ".tooltip-arrow{bottom:0;left:5px;border-width:5px 5px 0;border-top-color:#000}\n" \
    ".tooltip.top-right .tooltip-arrow{right:5px;bottom:0;border-width:5px 5px 0;border-top-color:#000}\n" \
    ".tooltip.right .tooltip-arrow{top:50%;left:0;margin-top:-5px;border-width:5px 5px 5px 0;border-right-color:#000}\n" \
    ".tooltip.left .tooltip-arrow{top:50%;right:0;margin-top:-5px;border-width:5px 0 5px 5px;border-left-color:#000}\n" \
    ".tooltip.bottom .tooltip-arrow{top:0;left:50%;margin-left:-5px;border-width:0 5px 5px;border-bottom-color:#000}\n" \
    ".tooltip.bottom-left .tooltip-arrow{top:0;left:5px;border-width:0 5px 5px;border-bottom-color:#000}\n" \
    ".tooltip.bottom-right .tooltip-arrow{top:0;right:5px;border-width:0 5px 5px;border-bottom-color:#000}\n" \
    "</style>\n" \
    "<link href=\"http://seiyria.com/bootstrap-slider/css/bootstrap-slider.css\" rel=\"stylesheet\">\n"\
    "<script type=\"text/javascript\">\n"
    
HTML_HEADER_SCRIPT_SECTION = HTML_HEADER_SCRIPT_SECTION.replace("HTML_CURRENT_VERSION_PLACE", HTML_CURRENT_VERSION)   

HTML_HEADER_SCRIPT_GOOGLE_CHARTS_LOAD = \
    "google.charts.load('current', {'packages':['corechart', 'bar', 'line', 'timeline']});\n" \
    "google.charts.setOnLoadCallback(drawMainStatsBars);\n" \
    "google.charts.setOnLoadCallback(drawPowerUpsBars);\n" \
    "google.charts.setOnLoadCallback(drawAllStreakTimelines);\n" \
    "google.charts.setOnLoadCallback(drawPowerUpsTimeline);\n" \
    "google.charts.setOnLoadCallback(drawPowerUpsTimelineVer2);\n"
    # "google.charts.setOnLoadCallback(drawStreakTimelines);\n"


# POINT battle progress
# "google.charts.setOnLoadCallback(drawBattleProgress);\n" \

# "google.charts.setOnLoadCallback(drawMainStats);\n" \

HTML_SCRIPT_BATTLE_PROGRESS_FUNCTION = \
    "function drawBattleProgress() {\n" \
    "var data_options_battle_progress = new google.visualization.DataTable();\n" \
    "data_options_battle_progress.addColumn('number', 'X');\n" \
    "ADD_COLUMN_LINES" \
    "data_options_battle_progress.addRows([\n" \
    "ADD_ROWS_LINES" \
    "]);\n" \
    "var options_battle_progress = {\n" \
	"chart: {\n" \
    "      title: 'Battle progress'\n" \
    "    },\n" \
    "    hAxis: {\n" \
    "      title: 'Time'\n" \
    "    },\n" \
    "    vAxis: {\n" \
    "      title: 'Frags'\n" \
    "    },\n" \
    "    series: {\n" \
    "      1: {curveType: 'function'}\n" \
    "    },\n" \
    "    pointSize: 7\n" \
    " };\n" \
    "var chart_battle_progress = new google.visualization.LineChart(document.getElementById('chart_battle_progress'));\n" \
    "chart_battle_progress.draw(data_options_battle_progress, options_battle_progress);\n" \
    "}\n"

HTML_SCRIPT_BATTLE_PROGRESS_ADD_COLUMN_LINE = "data_options_battle_progress.addColumn('number', 'PLAYER_NAME');\n"

#HTML_BATTLE_PROGRESS_DIV_TAG = "<table style=\"width: 100%;\"><tr><td><div id=\"chart_battle_progress\" align=\"center\" style=\"width: 1200px; height: 800px;\"></div></td></tr></table>\n"
HTML_BATTLE_PROGRESS_DIV_TAG = "<div id=\"chart_battle_progress\" align=\"center\" style=\"width: 100%; height: 800px;\"></div>\n"

# =========================================================================================================================================================

HTML_SCRIPT_MAIN_STATS_FUNCTION = \
    "function drawMainStats() {\n" \
    "var data_frags = google.visualization.arrayToDataTable([\n" \
    "['Name', 'Frags'],\n" \
    "ADD_FRAGS_ROWS" \
    "]);\n" \
    "var options_frags = {\n" \
    "  title: 'Frags'\n" \
    "};\n" \
    "var chart_frags = new google.visualization.PieChart(document.getElementById('piechart_frags'));\n" \
    "chart_frags.draw(data_frags, options_frags);\n" \
    "\n" \
    "var data_kills = google.visualization.arrayToDataTable([\n" \
    "['Name', 'Kills'],\n" \
    "ADD_KILLS_ROWS" \
    "]);\n" \
    "var options_kills = {\n" \
    "  title: 'Kills'\n" \
    "};\n" \
    "var chart_kills = new google.visualization.PieChart(document.getElementById('piechart_kills'));\n" \
    "chart_kills.draw(data_kills, options_kills); \n" \
    "\n" \
    "var data_deaths = google.visualization.arrayToDataTable([\n" \
    "['Name', 'Deaths'],\n" \
    "ADD_DEATHS_ROWS" \
    "]);\n" \
    "var options_deaths = {\n" \
    "  title: 'Deaths'\n" \
    "};\n" \
    "var chart_deaths = new google.visualization.PieChart(document.getElementById('piechart_deaths'));\n" \
    "chart_deaths.draw(data_deaths, options_deaths);\n" \
    "\n" \
    "var data_suicides = google.visualization.arrayToDataTable([\n" \
    "['Name', 'Suicides'],\n" \
    "ADD_SUICIDES_ROWS" \
    "]);\n" \
    "var options_suicides = {\n" \
    "  title: 'Suicides'\n" \
    "};\n" \
    "var chart_suicides = new google.visualization.PieChart(document.getElementById('piechart_suicides'));\n" \
    "chart_suicides.draw(data_suicides, options_suicides);\n" \
    "$(\"#main_stats\").attr(\"class\", \"symple-toggle state-closed\");\n" \
    "}\n"

HTML_MAIN_STATS_DIAGRAMM_DIV_TAG = \
  "<div class=\"wpb_text_column wpb_content_element \">\n" \
  "<div class=\"wpb_wrapper\">\n" \
  "  <div class=\"symple-toggle state-open\" id=\"main_stats\">\n" \
  "    <h2 class=\"symple-toggle-trigger \">Main Stats Diagrams</h2>\n" \
  "    <div class=\"symple-toggle-container symple-clearfix\">\n" \
  "      <table style=\"width: 100%;\">\n" \
  "        <tr>\n" \
  "          <td style=\"width: 25%\">\n" \
  "            <div id=\"piechart_frags\"></div>\n" \
  "          </td>\n" \
  "          <td style=\"width: 25%\">\n" \
  "            <div id=\"piechart_kills\"></div>\n" \
  "          </td>\n" \
  "          <td style=\"width: 25%\">\n" \
  "            <div id=\"piechart_deaths\"></div>\n" \
  "          </td>\n" \
  "          <td style=\"width: 25%\">\n" \
  "            <div id=\"piechart_suicides\"></div>\n" \
  "          </td>\n" \
  "        </tr>\n" \
  "      </table>\n" \
  "    </div>\n" \
  "  </div>\n" \
  "</div>\n" \
  "</div>\n";

# =========================================================================================================================================================

HTML_SCRIPT_MAIN_STATS_BARS_FUNCTION = \
    "function drawMainStatsBars() {\n" \
    "var data = google.visualization.arrayToDataTable([\n" \
    "ADD_HEADER_ROW" \
    "ADD_STATS_ROWS" \
    "]);\n" \
    "var options = {\n" \
    "  chart: {\n" \
    "    title: 'Main stats'\n" \
    "  },\n" \
    "  hAxis: {\n" \
    "    title: 'Count',\n" \
    "    minValue: 0,\n" \
    "  },\n" \
    "  vAxis: {\n" \
    "    title: ''\n" \
    "  },\n" \
    "  annotations: {\n" \
    "    alwaysOutside: true,\n" \
    "      textStyle: {\n" \
    "        fontSize: 16,\n" \
    "        auraColor:   'none',\n" \
    "        bold: true,\n" \
    "    },\n" \
    "    boxStyle: {\n" \
    "      stroke: '#1B1B1B',\n" \
    "      strokeWidth: 1\n" \
    "    }\n" \
    "  },\n" \
    "};\n" \
    "var barchart = new google.visualization.ColumnChart(document.getElementById('chart_main_stats'));\n" \
    "barchart.draw(data, options);\n" \
    "$(\"#main_stats_bars\").attr(\"class\", \"symple-toggle state-closed\");\n" \
    "}\n"

HTML_MAIN_STATS_BARS_DIV_TAG = \
  "<div class=\"wpb_text_column wpb_content_element \">\n" \
  "<div class=\"wpb_wrapper\">\n" \
  "  <div class=\"symple-toggle state-open\" id=\"main_stats_bars\">\n" \
  "    <h1 class=\"symple-toggle-trigger \">Main Stats</h2>\n "  \
  "    <div class=\"symple-toggle-container symple-clearfix\">\n" \
  "      <div id=\"chart_main_stats\" style=\"width: 90%; height:  500px;\"></div>\n" \
  "    </div>\n" \
  "  </div>\n" \
  "</div>\n" \
  "</div>\n";

# =========================================================================================================================================================

HTML_SCRIPT_POWER_UPS_BARS_FUNCTION = \
    "function drawPowerUpsBars() {\n" \
    "var data = google.visualization.arrayToDataTable([\n" \
    "ADD_HEADER_ROW" \
    "ADD_STATS_ROWS" \
    "]);\n" \
    "var options = {\n" \
    "  chart: {\n" \
    "    title: 'Power Ups'\n" \
    "  },\n" \
    "  hAxis: {\n" \
    "    title: 'Count',\n" \
    "    minValue: 0,\n" \
    "  },\n" \
    "  vAxis: {\n" \
    "    title: ''\n" \
    "  },\n" \
    "  annotations: {\n" \
    "    alwaysOutside: true,\n" \
    "      textStyle: {\n" \
    "        fontSize: 16,\n" \
    "        auraColor:   'none',\n" \
    "        bold: true,\n" \
    "    },\n" \
    "    boxStyle: {\n" \
    "      stroke: '#1B1B1B',\n" \
    "      strokeWidth: 1\n" \
    "    }\n" \
    "  },\n" \
    "};\n" \
    "var barchart = new google.visualization.ColumnChart(document.getElementById('chart_power_ups'));\n" \
    "barchart.draw(data, options);\n" \
    "$(\"#power_ups_bars\").attr(\"class\", \"symple-toggle state-closed\");\n" \
    "}\n"

HTML_POWER_UPS_BARS_DIV_TAG = \
  "<div class=\"wpb_text_column wpb_content_element \">\n" \
  "<div class=\"wpb_wrapper\">\n" \
  "  <div class=\"symple-toggle state-open\" id=\"power_ups_bars\">\n" \
  "    <h2 class=\"symple-toggle-trigger \">Power Ups</h2>\n" \
  "    <div class=\"symple-toggle-container symple-clearfix\">\n" \
  "      <div id=\"chart_power_ups\" style=\"width: 90%; height:  450px;\"></div>\n" \
  "    </div>\n" \
  "  </div>\n" \
  "</div>\n" \
  "</div>\n";

# =========================================================================================================================================================

HTML_SCRIPT_TEAM_RESULTS_FUNCTION = \
"function drawTeamResults() {\n" \
"      var data = google.visualization.arrayToDataTable([\n" \
"ADD_HEADER_ROW" \
"ADD_STATS_ROWS" \
"      ]);\n" \
"      var options = {\n" \
"        title: 'Game score',\n" \
"        chartArea: {width: '100%'},\n" \
"        hAxis: {\n" \
"          title: '',\n" \
"          minValue: 0,\n" \
"          ticks: [0.4,0.5,0.6]\n" \
"        },\n" \
"        isStacked: 'relative',\n" \
"        legend: 'none',\n" \
"animation:{\n" \
"        duration: 500,\n" \
"        easing: 'out',\n" \
"        startup: true\n" \
"      },\n" \
"   annotations: {\n" \
"    textStyle: {\n" \
"      fontName: 'Times-Roman',\n" \
"      fontSize: 45,\n" \
"      bold: true,\n" \
"      color: '#871b47',\n" \
"      auraColor: '#d799ae',\n" \
"      opacity: 1\n" \
"     }\n" \
"    }\n" \
"  };\n" \
"      var chart = new google.visualization.BarChart(document.getElementById('chart_team_results'));\n" \
"      chart.draw(data, options);\n" \
"    }\n"

HTML_TEAM_RESULTS_FUNCTION_DIV_TAG = "<div id=\"chart_team_results\" style=\"min-width: 30px;  height: 150px; margin: 0 auto\"></div>\n"

# =========================================================================================================================================================

HTML_SCRIPT_POWER_UPS_BY_MINUTES_FUNCTION =\
    "google.charts.setOnLoadCallback(drawPOWER_UP_NAMEByMinutes);\n" \
    "function drawPOWER_UP_NAMEByMinutes() {\n" \
    "var data = google.visualization.arrayToDataTable([\n" \
    "ADD_HEADER_ROW" \
    "ADD_STATS_ROWS" \
    "]);\n" \
    "var dataTotal = google.visualization.arrayToDataTable([\n" \
    "ADD_TOTAL_HEADER_ROW" \
    "ADD_TOTAL_STATS_ROWS" \
    "]);\n" \
    "\n" \
    "var options = {\n" \
    "  isStacked: false,\n" \
    "  height: 300,\n" \
    "  \n" \
    "  legend: { position: 'right', maxLines: 2 },\n" \
    "  title: \"POWER_UP_NAME by minutes\"\n" \
    "};\n" \
    "var optionsTotal = {\n" \
    "  isStacked: false,\n" \
    "  height: 300,\n" \
    "  legend: { position: \"none\" },\n" \
    "  title: \"POWER_UP_NAME total\"\n" \
    "};\n" \
    "\n" \
    "var chart      = new google.visualization.ColumnChart(document.getElementById('POWER_UP_NAME_div'));\n" \
    "var chartTotal = new google.visualization.ColumnChart(document.getElementById('POWER_UP_NAME_total_div'));\n" \
    "\n" \
    "chart.draw(data, options);\n" \
    "chartTotal.draw(dataTotal, optionsTotal);\n" \
    "$(\"#POWER_UP_NAME_by_minutes\").attr(\"class\", \"symple-toggle state-closed\");\n" \
    "}\n"

#options:
#    "  vAxis: {minValue: MIN_VALUE, maxValue: MAX_VALUE},\n" \
#    "  vAxis: {minValue: TOTAL_MIN__VALUE, maxValue: TOTAL_MAX__VALUE},\n" \

HTML_POWER_UPS_BY_MINUTES_DIV_TAG = \
  "<div class=\"wpb_text_column wpb_content_element \">\n" \
  "<div class=\"wpb_wrapper\">\n" \
  "  <div class=\"symple-toggle state-open\" id=\"POWER_UP_NAME_by_minutes\">\n" \
  "    <h2 class=\"symple-toggle-trigger \">POWER_UP_NAME by minutes</h3>\n " \
  "    <div class=\"symple-toggle-container symple-clearfix\">\n" \
  "      <table style=\"width: 100%;\">\n" \
  "        <tr>\n" \
  "          <td style=\"width: 83%\">\n" \
  "            <div id=\"POWER_UP_NAME_div\" style=\"width:  100%; height:  300px;\"></div>\n" \
  "          </td>\n" \
  "          <td style=\"width: 17%\">\n" \
  "            <div id=\"POWER_UP_NAME_total_div\" style=\"width:  100%; height:  300px;\"></div>\n" \
  "          </td>\n" \
  "        </tr>\n" \
  "      </table>\n" \
  "    </div>\n" \
  "  </div>\n" \
  "</div>\n" \
  "</div>\n";

# =========================================================================================================================================================

HTML_SCRIPT_HIGHCHARTS_POWER_UPS_FUNCTIONS = \
"$(function () {\n" \
"Highcharts.theme = {\n" \
"   chart: {\n" \
"      backgroundColor: null,\n" \
"      style: {\n" \
"         fontFamily: \"Dosis, sans-serif\"\n" \
"      }\n" \
"   },\n" \
"   title: {\n" \
"      style: {\n" \
"         fontSize: '16px',\n" \
"         fontWeight: 'bold',\n" \
"         textTransform: 'uppercase'\n" \
"      }\n" \
"   },\n" \
"   tooltip: {\n" \
"      borderWidth: 0,\n" \
"      backgroundColor: 'rgba(219,219,216,0.8)',\n" \
"      shadow: false\n" \
"   },\n" \
"   legend: {\n" \
"      itemStyle: {\n" \
"         fontWeight: 'bold',\n" \
"         fontSize: '13px'\n" \
"      }\n" \
"   },\n" \
"   xAxis: {\n" \
"      \n" \
"      gridLineWidth: 1,\n" \
"      labels: {\n" \
"         style: {\n" \
"            fontSize: '12px'\n" \
"         }\n" \
"      }\n" \
"   },\n" \
"   yAxis: {\n" \
"      title: {\n" \
"         style: {\n" \
"            textTransform: 'uppercase'\n" \
"         }\n" \
"      },\n" \
"      labels: {\n" \
"         style: {\n" \
"            fontSize: '12px'\n" \
"         }\n" \
"      }\n" \
"   },\n" \
"   plotOptions: {\n" \
"      candlestick: {\n" \
"         lineColor: '#404048'\n" \
"      }\n" \
"   },\n" \
"\n" \
"\n" \
"   // General\n" \
"   background2: '#F0F0EA'\n" \
"\n" \
"};\n" \
"\n" \
"// Apply the theme\n" \
"Highcharts.setOptions(Highcharts.theme);\n" \
"\n" \
"    $('#highchart_power_up_ra').highcharts({\n" \
"        chart: {\n" \
"                type: 'area',\n" \
"                zoomType: 'x'\n" \
"            },\n" \
"        title: {\n" \
"            text: 'Red Armor',\n" \
"            x: -20 //center\n" \
"        },\n" \
"        subtitle: {\n" \
"            text: '',\n" \
"            x: -20\n" \
"        },\n" \
"        xAxis: {\n" \
"            title: {\n" \
"                text: 'Time'\n" \
"            },\n" \
"        },\n" \
"        yAxis: {\n" \
"            title: {\n" \
"                text: 'Count'\n" \
"            },\n" \
"            plotLines: [{\n" \
"                value: 0,\n" \
"                width: 1,\n" \
"                color: '#808080'\n" \
"            }]\n" \
"        },\n" \
"        tooltip: {\n" \
"            valueSuffix: ''\n" \
"        },\n" \
"        plotOptions: {\n" \
"            area: {\n" \
"                stacking: 'normal',\n" \
"            }\n" \
"        },\n" \
"        legend: {\n" \
"            layout: 'vertical',\n" \
"            align: 'right',\n" \
"            verticalAlign: 'middle', \n" \
"            borderWidth: 0\n" \
"        },\n" \
"        series: [{\n" \
"ADD_STAT_ROWS_ra" \
"        }]\n" \
"    });\n" \
"    $('#highchart_power_up_ya').highcharts({\n" \
"        chart: {\n" \
"                type: 'area',\n" \
"                zoomType: 'x'\n" \
"            },\n" \
"        title: {\n" \
"            text: 'Yellow Armor',\n" \
"            x: -20 //center\n" \
"        },\n" \
"        subtitle: {\n" \
"            text: '',\n" \
"            x: -20\n" \
"        },\n" \
"        xAxis: {\n" \
"            title: {\n" \
"                text: 'Time'\n" \
"            },\n" \
"        },\n" \
"        yAxis: {\n" \
"            title: {\n" \
"                text: 'Count'\n" \
"            },\n" \
"            plotLines: [{\n" \
"                value: 0,\n" \
"                width: 1,\n" \
"                color: '#808080'\n" \
"            }]\n" \
"        },\n" \
"        tooltip: {\n" \
"            valueSuffix: ''\n" \
"        },\n" \
"        plotOptions: {\n" \
"            area: {\n" \
"                stacking: 'normal',\n" \
"            }\n" \
"        },\n" \
"        legend: {\n" \
"            layout: 'vertical',\n" \
"            align: 'right',\n" \
"            verticalAlign: 'middle', \n" \
"            borderWidth: 0\n" \
"        },\n" \
"        series: [{\n" \
"ADD_STAT_ROWS_ya" \
"        }]\n" \
"    });\n" \
"    $('#highchart_power_up_ga').highcharts({\n" \
"        chart: {\n" \
"                type: 'area',\n" \
"                zoomType: 'x'\n" \
"            },\n" \
"        title: {\n" \
"            text: 'Green Armor',\n" \
"            x: -20 //center\n" \
"        },\n" \
"        subtitle: {\n" \
"            text: '',\n" \
"            x: -20\n" \
"        },\n" \
"        xAxis: {\n" \
"            title: {\n" \
"                text: 'Time'\n" \
"            },\n" \
"        },\n" \
"        yAxis: {\n" \
"            title: {\n" \
"                text: 'Count'\n" \
"            },\n" \
"            plotLines: [{\n" \
"                value: 0,\n" \
"                width: 1,\n" \
"                color: '#808080'\n" \
"            }]\n" \
"        },\n" \
"        tooltip: {\n" \
"            valueSuffix: ''\n" \
"        },\n" \
"        plotOptions: {\n" \
"            area: {\n" \
"                stacking: 'normal',\n" \
"            }\n" \
"        },\n" \
"        legend: {\n" \
"            layout: 'vertical',\n" \
"            align: 'right',\n" \
"            verticalAlign: 'middle', \n" \
"            borderWidth: 0\n" \
"        },\n" \
"        series: [{\n" \
"ADD_STAT_ROWS_ga" \
"        }]\n" \
"    });\n" \
"    $('#highchart_power_up_mh').highcharts({\n" \
"        chart: {\n" \
"                type: 'area',\n" \
"                zoomType: 'x'\n" \
"            },\n" \
"        title: {\n" \
"            text: 'Mega Health',\n" \
"            x: -20 //center\n" \
"        },\n" \
"        subtitle: {\n" \
"            text: '',\n" \
"            x: -20\n" \
"        },\n" \
"        xAxis: {\n" \
"            title: {\n" \
"                text: 'Time'\n" \
"            },\n" \
"        },\n" \
"        yAxis: {\n" \
"            title: {\n" \
"                text: 'Count'\n" \
"            },\n" \
"            plotLines: [{\n" \
"                value: 0,\n" \
"                width: 1,\n" \
"                color: '#808080'\n" \
"            }]\n" \
"        },\n" \
"        tooltip: {\n" \
"            valueSuffix: ''\n" \
"        },\n" \
"        plotOptions: {\n" \
"            area: {\n" \
"                stacking: 'normal',\n" \
"            }\n" \
"        },\n" \
"        legend: {\n" \
"            layout: 'vertical',\n" \
"            align: 'right',\n" \
"            verticalAlign: 'middle', \n" \
"            borderWidth: 0\n" \
"        },\n" \
"        series: [{\n" \
"ADD_STAT_ROWS_mh" \
"        }]\n" \
"    });\n" \
"$(\"#PowerUpsByMinutes\").attr(\"class\", \"symple-toggle state-closed\");\n" \
"});\n" \

HTML_SCRIPT_HIGHCHARTS_POWER_UPS_DIVS_TAG = \
  "<div class=\"wpb_text_column wpb_content_element \">\n" \
  "<div class=\"wpb_wrapper\">\n" \
  "  <div class=\"symple-toggle state-open\" id=\"PowerUpsByMinutes\">\n" \
  "    <h2 class=\"symple-toggle-trigger \">Power Ups by minutes</h3>\n " \
  "    <div class=\"symple-toggle-container symple-clearfix\">\n" \
  "<div id=\"highchart_power_up_ra\" style=\"min-width: 30px;  height: 400px; margin: 0 auto\"></div>\n" \
  "<div id=\"highchart_power_up_ya\" style=\"min-width: 310px; height: 400px; margin: 0 auto\"></div>\n" \
  "<div id=\"highchart_power_up_ga\" style=\"min-width: 310px; height: 400px; margin: 0 auto\"></div>\n" \
  "<div id=\"highchart_power_up_mh\" style=\"min-width: 310px; height: 400px; margin: 0 auto\"></div>\n" \
  "    </div>\n" \
  "  </div>\n" \
  "</div>\n" \
  "</div>\n";

# =========================================================================================================================================================

HTML_SCRIPT_PLAYER_KILLS_BY_MINUTES_FUNCTION =\
    "google.charts.setOnLoadCallback(drawPLAYER_NAMEKillsByMinutes);\n" \
    "function drawPLAYER_NAMEKillsByMinutes() {\n" \
    "var data = google.visualization.arrayToDataTable([\n" \
    "ADD_HEADER_ROW" \
    "ADD_STATS_ROWS" \
    "]);\n" \
    "var dataTotal = google.visualization.arrayToDataTable([\n" \
    "ADD_TOTAL_HEADER_ROW" \
    "ADD_TOTAL_STATS_ROWS" \
    "]);\n" \
    "\n" \
    "var options = {\n" \
    "  isStacked: true,\n" \
    "  height: 300,\n" \
    "  \n" \
    "  vAxis: {minValue: MIN_VALUE, maxValue: MAX_VALUE},\n" \
    "  legend: { position: 'right', maxLines: 2 },\n" \
    "  title: \"PLAYER_NAME kills by minutes\"\n" \
    "};\n" \
    "var optionsTotal = {\n" \
    "  isStacked: false,\n" \
    "  height: 300,\n" \
    "  vAxis: {minValue: TOTAL_MIN__VALUE, maxValue: TOTAL_MAX__VALUE},\n" \
    "  legend: { position: \"none\" },\n" \
    "  title: \"PLAYER_NAME total kills\"\n" \
    "};\n" \
    "\n" \
    "var chart      = new google.visualization.ColumnChart(document.getElementById('PLAYER_NAME_kills_div'));\n" \
    "var chartTotal = new google.visualization.ColumnChart(document.getElementById('PLAYER_NAME_total_kills_div'));\n" \
    "\n" \
    "chart.draw(data, options);\n" \
    "chartTotal.draw(dataTotal, optionsTotal);\n" \
    "$(\"#PLAYER_NAME_kills_by_minutes\").attr(\"class\", \"symple-toggle state-closed\");\n" \
    "}\n"

HTML_PLAYER_KILLS_BY_MINUTES_DIV_TAG = \
  "<div class=\"wpb_text_column wpb_content_element \">\n" \
  "<div class=\"wpb_wrapper\">\n" \
  "  <div class=\"symple-toggle state-open\" id=\"PLAYER_NAME_kills_by_minutes\">\n" \
  "    <h3 class=\"symple-toggle-trigger \">PLAYER_NAME Kills by minutes</h3>\n" \
  "    <div class=\"symple-toggle-container symple-clearfix\">\n" \
  "      <table style=\"width: 100%;\">\n" \
  "        <tr>\n" \
  "          <td style=\"width: 83%\">\n" \
  "            <div id=\"PLAYER_NAME_kills_div\" style=\"width:  100%; height:  300px;\"></div>\n" \
  "          </td>\n" \
  "          <td style=\"width: 17%\">\n" \
  "            <div id=\"PLAYER_NAME_total_kills_div\" style=\"width:  100%; height:  300px;\"></div>\n" \
  "          </td>\n" \
  "        </tr>\n" \
  "      </table>\n" \
  "    </div>\n" \
  "  </div>\n" \
  "</div>\n" \
  "</div>\n";

# =========================================================================================================================================================

HTML_SCRIPT_STREAK_TIMELINE_FUNCTION = \
    "function drawStreakTimelines() {\n" \
    "var container = document.getElementById('streak_chart_timeline_div');\n" \
    "var chart = new google.visualization.Timeline(container);\n" \
    "var dataTable = new google.visualization.DataTable();\n" \
    "dataTable.addColumn({ type: 'string', id: 'Position' });\n" \
    "dataTable.addColumn({ type: 'string', id: 'Name' });\n" \
    "dataTable.addColumn({ type: 'date', id: 'Start' });\n" \
    "dataTable.addColumn({ type: 'date', id: 'End' });\n" \
    "dataTable.addRows([\n" \
    "ADD_STATS_ROWS" \
    "]);" \
    "var options = { timeline: { singleColor: '#8d8' ,\n" \
    "                            rowLabelStyle: { fontName: 'Helvetica', fontSize: 20 },\n" \
    "                            barLabelStyle: { fontName: 'Garamond',  fontSize: 9 } } };\n" \
    "chart.draw(dataTable, options) ;\n" \
    "\n" \
    "var deathcontainer = document.getElementById('death_streak_chart_timeline_div');\n" \
    "var deathchart = new google.visualization.Timeline(deathcontainer);\n" \
    "var deathdataTable = new google.visualization.DataTable();\n" \
    "deathdataTable.addColumn({ type: 'string', id: 'Position' });\n" \
    "deathdataTable.addColumn({ type: 'string', id: 'Name' });\n" \
    "deathdataTable.addColumn({ type: 'date', id: 'Start' });\n" \
    "deathdataTable.addColumn({ type: 'date', id: 'End' });\n" \
    "deathdataTable.addRows([\n" \
    "ADD_DEATH_STATS_ROWS" \
    "]);" \
    "var deathoptions = { timeline: { singleColor: 'red' ,\n" \
    "                            rowLabelStyle: { fontName: 'Helvetica', fontSize: 16 },\n" \
    "                            barLabelStyle: { fontName: 'Garamond',  fontSize:  9, fontPosition: 'center'  } } };\n" \
    "deathchart.draw(deathdataTable, deathoptions) ;\n" \
    "}"

HTML_SCRIPT_STREAK_TIMELINE_DIV_TAG = \
  "      <table style=\"width: 100%;\">\n" \
  "        <tr>\n" \
  "          <td style=\"width: 50%\">\n" \
  "            <div id=\"streak_chart_timeline_div\" style=\"width:  100%; height: 400px;\"></div>\n" \
  "          </td>\n" \
  "          <td style=\"width: 50%\">\n" \
  "            <div id=\"death_streak_chart_timeline_div\" style=\"width:  100%; height: 400px;\"></div>\n" \
  "          </td>\n" \
  "        </tr>\n" \
  "      </table>\n" \

# =========================================================================================================================================================

HTML_SCRIPT_ALL_STREAK_TIMELINE_FUNCTION = \
    "function drawAllStreakTimelines(num) {\n" \
    "if (num == undefined) { num = 3 }\n" \
    "var container = document.getElementById('all_streak_chart_timeline_div');\n" \
    "var chart = new google.visualization.Timeline(container);\n" \
    "var dataTable = new google.visualization.DataTable();\n" \
    "dataTable.addColumn({ type: 'string', id: 'Position' });\n" \
    "dataTable.addColumn({ type: 'string', id: 'Name' });\n" \
    "dataTable.addColumn({ type: 'string', role: 'tooltip', 'p': {'html': true} });\n" \
    "dataTable.addColumn({ type: 'date', id: 'Start' });\n" \
    "dataTable.addColumn({ type: 'date', id: 'End' });\n" \
    "var allRows = [\n"\
    "ALL_ROWS" \
    "];\n" \
    "var currentRows = [\n"\
    "CURRENT_ROWS" \
    "];\n" \
    "for (var i = 0; i < allRows.length; i++) {\n" \
    "var vv = parseInt(allRows[i][1])\n" \
    "if (vv >= num) {\n" \
    "currentRows.push(allRows[i])\n" \
    "}\n" \
    "}\n" \
    "dataTable.addRows(currentRows);\n" \
    "var options = { colors: ['#8d8', 'red'],\n" \
    "                timeline: { colorByRowLabel: true, rowLabelStyle: { fontName: 'Helvetica', fontSize: 16 },\n" \
    "                            barLabelStyle: { fontName: 'Garamond',  fontSize: 9, fontPosition: 'center'  } } };\n" \
    "chart.draw(dataTable, options) ;\n" \
    "}"

HTML_SCRIPT_ALL_STREAK_TIMELINE_DIV_TAG = \
  "      <table style=\"width: 100%;\">\n" \
  "        <tr>\n" \
  "          <td rowspan=\"3\" style=\"width: 95%\">\n" \
  "            <div id=\"all_streak_chart_timeline_div\" style=\"width: 100%; height: HEIGHT_IN_PXpx;\"></div>\n" \
  "          </td>\n" \
  "          <td style=\"width: 2%\">\n" \
  "          </td>\n" \
  "          <td style=\"width: 3%\">\n" \
  "            <div id=\"timeline_slider\" data-slider-id='timeline_slider' />\n" \
  "          </td>\n" \
  "        </tr>\n" \
  "        <tr style=\"height: 30px;\"></tr>\n" \
  "      </table>\n"
#  "<input type=\"range\" min=\"1\" max=\"15\" step=\"1\" value=\"3\" size=\"100\" onchange=\"drawAllStreakTimelines(this.value)\">\n"

# =========================================================================================================================================================

HTML_SCRIPT_POWER_UPS_TIMELINE_FUNCTION = \
    "function drawPowerUpsTimeline() {\n" \
    "var container = document.getElementById('power_ups_timeline_div');\n" \
    "var chart = new google.visualization.Timeline(container);\n" \
    "var dataTable = new google.visualization.DataTable();\n" \
    "dataTable.addColumn({ type: 'string', id: 'Position' });\n" \
    "dataTable.addColumn({ type: 'string', id: 'Name' });\n" \
    "dataTable.addColumn({ type: 'string', role: 'tooltip' });\n" \
    "dataTable.addColumn({ type: 'date', id: 'Start' });\n" \
    "dataTable.addColumn({ type: 'date', id: 'End' });\n" \
    "var allRows = [\n"\
    "ALL_ROWS" \
    "];\n" \
    "dataTable.addRows(allRows);\n" \
    "var options = { colors: ['gray', 'red','yellow','green','#660066'], \n" \
    "                timeline: { colorByRowLabel: true, rowLabelStyle: { fontName: 'Helvetica', fontSize: 16 },\n" \
    "                            barLabelStyle: { fontName: 'Garamond',  fontSize: 9, fontPosition: 'center'  } } };\n" \
    "chart.draw(dataTable, options) ;\n" \
    "$(\"#PowerUpsTimeline\").attr(\"class\", \"symple-toggle state-closed\");\n" \
    "}"

# HTML_SCRIPT_POWER_UPS_TIMELINE_DIV_TAG = "<div id=\"power_ups_timeline_div\" style=\"width: 100%; height: HEIGHT_IN_PXpx;\"></div>\n"

HTML_SCRIPT_POWER_UPS_TIMELINE_DIV_TAG = \
  "<div class=\"wpb_text_column wpb_content_element \">\n" \
  "<div class=\"wpb_wrapper\">\n" \
  "  <div class=\"symple-toggle state-open\" id=\"PowerUpsTimeline\">\n" \
  "    <h2 class=\"symple-toggle-trigger \">Power Ups timeline ver.1</h3>\n " \
  "    <div class=\"symple-toggle-container symple-clearfix\">\n" \
  "<div id=\"power_ups_timeline_div\" style=\"width: 100%; height: HEIGHT_IN_PXpx;\"></div>\n" \
  "    </div>\n" \
  "  </div>\n" \
  "</div>\n" \
  "</div>\n";

# =========================================================================================================================================================

HTML_SCRIPT_POWER_UPS_TIMELINE_VER2_FUNCTION = \
    "function drawPowerUpsTimelineVer2() {\n" \
    "var container = document.getElementById('power_ups_timeline_ver2_div');\n" \
    "var chart = new google.visualization.Timeline(container);\n" \
    "var dataTable = new google.visualization.DataTable();\n" \
    "dataTable.addColumn({ type: 'string', id: 'Position' });\n" \
    "dataTable.addColumn({ type: 'string', id: 'Name' });\n" \
    "dataTable.addColumn({ type: 'string', role: 'tooltip' });\n" \
    "dataTable.addColumn({ type: 'date', id: 'Start' });\n" \
    "dataTable.addColumn({ type: 'date', id: 'End' });\n" \
    "var allRows = [\n"\
    "ALL_ROWS" \
    "];\n" \
    "dataTable.addRows(allRows);\n" \
    "var options = { colors: [COLORS], \n" \
    "                timeline: { colorByRowLabel: true, rowLabelStyle: { fontName: 'Helvetica', fontSize: 16 },\n" \
    "                            barLabelStyle: { fontName: 'Garamond',  fontSize: 9, fontPosition: 'center'  } } };\n" \
    "chart.draw(dataTable, options) ;\n" \
    "$(\"#PowerUpsTimelineVer2\").attr(\"class\", \"symple-toggle state-closed\");\n" \
    "}"

# HTML_SCRIPT_POWER_UPS_TIMELINE_DIV_TAG = "<div id=\"power_ups_timeline_div\" style=\"width: 100%; height: HEIGHT_IN_PXpx;\"></div>\n"

HTML_SCRIPT_POWER_UPS_TIMELINE_VER2_DIV_TAG = \
  "<div class=\"wpb_text_column wpb_content_element \">\n" \
  "<div class=\"wpb_wrapper\">\n" \
  "  <div class=\"symple-toggle state-open\" id=\"PowerUpsTimelineVer2\">\n" \
  "    <h2 class=\"symple-toggle-trigger \">Power Ups timeline ver.2</h3>\n " \
  "    <div class=\"symple-toggle-container symple-clearfix\">\n" \
  "<div id=\"power_ups_timeline_ver2_div\" style=\"width: 100%; height: HEIGHT_IN_PXpx;\"></div>\n" \
  "    </div>\n" \
  "  </div>\n" \
  "</div>\n" \
  "</div>\n";

# =========================================================================================================================================================

HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION = \
"$(function () {\n" \
"Highcharts.theme = {\n" \
"   chart: {\n" \
"      backgroundColor: null,\n" \
"      style: {\n" \
"         fontFamily: \"Dosis, sans-serif\"\n" \
"      }\n" \
"   },\n" \
"   title: {\n" \
"      style: {\n" \
"         fontSize: '16px',\n" \
"         fontWeight: 'bold',\n" \
"         textTransform: 'uppercase'\n" \
"      }\n" \
"   },\n" \
"   tooltip: {\n" \
"      borderWidth: 0,\n" \
"      backgroundColor: 'rgba(219,219,216,0.8)',\n" \
"      shadow: false\n" \
"   },\n" \
"   legend: {\n" \
"      itemStyle: {\n" \
"         fontWeight: 'bold',\n" \
"         fontSize: '13px'\n" \
"      }\n" \
"   },\n" \
"   xAxis: {\n" \
"      \n" \
"      gridLineWidth: 1,\n" \
"      labels: {\n" \
"         style: {\n" \
"            fontSize: '12px'\n" \
"         }\n" \
"      }\n" \
"   },\n" \
"   yAxis: {\n" \
"      title: {\n" \
"         style: {\n" \
"            textTransform: 'uppercase'\n" \
"         }\n" \
"      },\n" \
"      labels: {\n" \
"         style: {\n" \
"            fontSize: '12px'\n" \
"         }\n" \
"      },\n" \
"MIN_PLAYER_FRAGS\n" \
"MAX_PLAYER_FRAGS\n" \
"   },\n" \
"   plotOptions: {\n" \
"      candlestick: {\n" \
"         lineColor: '#404048'\n" \
"      }\n" \
"   },\n" \
"\n" \
"\n" \
"   // General\n" \
"   background2: '#F0F0EA'\n" \
"\n" \
"};\n" \
"\n" \
"// Apply the theme\n" \
"Highcharts.setOptions(Highcharts.theme);\n" \
"\n" \
"    $('#highchart_battle_progress').highcharts({\n" \
"        chart: {\n" \
"                zoomType: 'x'\n" \
"            },\n" \
"        title: {\n" \
"            text: 'GRAPH_TITLE',\n" \
"            x: -20 //center\n" \
"        },\n" \
"        subtitle: {\n" \
"            text: '',\n" \
"            x: -20\n" \
"        },\n" \
"        xAxis: {\n" \
"            title: {\n" \
"                text: 'Time'\n" \
"            },\n" \
"EXTRA_XAXIS_OPTIONS" \
"        },\n" \
"        yAxis: {\n" \
"            title: {\n" \
"                text: 'Y_AXIS_TITLE'\n" \
"            },\n" \
"            plotLines: [{\n" \
"                value: 0,\n" \
"                width: 1,\n" \
"                color: '#808080'\n" \
"            }]\n" \
"        },\n" \
"        tooltip: {\n" \
"TOOLTIP_STYLE" \
"        },\n" \
"        legend: {\n" \
"            layout: 'vertical',\n" \
"            align: 'right',\n" \
"            verticalAlign: 'middle',\n" \
"            borderWidth: 0\n" \
"        },\n" \
"        series: [{\n" \
"ADD_STAT_ROWS" \
"        }]\n" \
"    });\n" \
"});\n" \

HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_TOOLTIP_SIMPLE = \
"             shared: false,\n " \
"	          formatter: null,\n"

HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_TOOLTIP_SORTED = \
"            valueSuffix: '',\n" \
"            shared: true,\n" \
"            formatter: function() {\n" \
"            var s = '<strong>'+ this.x +'</strong>';\n" \
"            var sortedPoints = this.points.sort(function(a, b){\n" \
"                  return ((a.y < b.y) ? 1 : ((a.y > b.y) ? -1 : 0));\n  " \
"              });\n" \
"            $.each(sortedPoints , function(i, point) {\n" \
"            s += '<br/>'+ point.series.name +': '+ point.y;\n" \
"            });\n" \
"            return s;\n" \
"            },\n"

HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_DIV_TAG = "<div id=\"highchart_battle_progress\" style=\"min-width: 310px; height: 500px; margin: 0 auto\"></div>"
HTML_SCRIPT_HIGHCHARTS_EXTENDED_BATTLE_PROGRESS_DIV_TAG = "<div id=\"highchart_battle_progress_extended\" style=\"min-width: 310px; height: 500px; margin: 0 auto\"></div>"

HIGHCHARTS_BATTLE_PROGRESS_GRANULARITY = 4

HTML_SCRIPT_HIGHCHARTS_PLAYERS_RANK_PROGRESS_DIV_TAG = \
  "      <table style=\"width: 100%;\">\n" \
  "        <tr>\n" \
  "          <td style=\"width: 50%\">\n" \
  "            <div id=\"players_rank1\" style=\"height: 400px; margin: 0 auto\"></div>\n" \
  "          </td>\n" \
  "          <td style=\"width: 50%\">\n" \
  "            <div id=\"players_rank2\" style=\"height: 400px; margin: 0 auto\"></div>\n" \
  "          </td>\n" \
  "        </tr>\n" \
  "      </table>\n" \

HTML_SCRIPT_HIGHCHARTS_DEATHMATCH_PLAYERS_RANK_PROGRESS_DIV_TAG = "<div id=\"players_rank\" style=\"height: 400px; margin: 0 auto\"></div>\n"

HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_X_AXIS_LABELS_TICK_POSITIONS = \
"labels: {\n" \
"     formatter: function () {\n" \
"       return (this.value / 60).toFixed(1).toString()\n" \
"    },\n" \
"},\n" \
"tickPositions: [TICK_POSITIONS_VALS],\n"

HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_X_AXIS_LABELS_VERTICAL_LINE = \
"    plotLines: [{\n" \
"        color: '#FF0000', // Red\n" \
"        width: 7,\n" \
"        value: VERTICAL_LINE_POS // Position, you'll have to translate this to the values on your x axis\n" \
"    }]\n"

# =========================================================================================================================================================
# "            categories: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']\n" \

HTML_SCRIPT_HIGHCHARTS_TEAM_BATTLE_PROGRESS_FUNCTION = \
"$(function () {\n" \
"    Highcharts.chart('DIV_NAME', {\n" \
"        chart: {\n " \
"            zoomType: 'x'\n " \
"        },\n " \
"        title: {\n" \
"            text: 'TEAM_NAME'\n" \
"        },\n" \
"        xAxis: {\n" \
"            categories: [MINUTES],\n" \
"            crosshair: true,\n" \
"            labels: {\n" \
"     formatter: function () {\n" \
"       return (this.value).toString()\n" \
"    },\n" \
"},\n" \
"            tickPositions: [TICK_POSITIONS_VALS]\n" \
"        },\n" \
"        yAxis: [{\n" \
"            title: {\n" \
"                text: 'Player Frags'\n" \
"            },\n" \
"            opposite: true,\n" \
"            min: 0,\n" \
"            max: MAX_PLAYER_FRAGS\n" \
"        }, {\n" \
"	         gridLineWidth: 0,\n" \
"            title: {\n" \
"                text: 'Total Frags',\n" \
"            },\n" \
"            min: 0,\n" \
"            max: MAX_TOTAL_FRAGS\n" \
"        }],\n" \
"        tooltip: {\n" \
"            valueSuffix: '',\n" \
"            shared: true,\n" \
"            formatter: function() {\n" \
"            var s = '<strong>'+ this.x +'</strong>';\n" \
"            var sortedPoints = this.points.sort(function(a, b){\n" \
"                  return ((a.y < b.y) ? 1 : ((a.y > b.y) ? -1 : 0));\n" \
"                });\n" \
"            $.each(sortedPoints , function(i, point) {\n" \
"            s += '<br/>'+ point.series.name +': '+ '<strong>' + point.y + '</strong>';\n" \
"            });\n" \
"            return s;\n" \
"            },\n" \
"        },\n" \
"        legend: {\n" \
"            layout: 'vertical',\n" \
"            align: 'left',\n" \
"            x: 180,\n" \
"            verticalAlign: 'top',\n" \
"            y: 55,\n" \
"            floating: true,\n" \
"            backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF'\n" \
"        },\n" \
"        series: [\n" \
"ADD_ROWS" \
"        {\n" \
"            type: 'spline',\n" \
"            name: 'Team score',\n" \
"            data: [TEAM_POINTS],\n" \
"            lineWidth: 8,\n" \
"            yAxis: 1,\n" \
"            marker: {\n" \
"                lineWidth: 3,\n" \
"                lineColor: Highcharts.getOptions().colors[3],\n" \
"                fillColor: 'white'\n" \
"            }\n" \
"        }\n" \
"      ]\n" \
"    });\n" \
"});\n"

HTML_SCRIPT_HIGHCHARTS_TEAM_BATTLE_PROGRESS_PLAYER_SECTION = \
"        {\n" \
"            type: 'column',\n" \
"            name: 'PLAYER_NAME',\n" \
"            data: [PLAYER_POINTS]\n" \
"        },\n" \

HTML_SCRIPT_HIGHCHARTS_TEAM_BATTLE_PROGRESS_DIV_TAG_TEAM1 = "<div id=\"team_progress1\" style=\"min-width: 310px; height: 400px; margin: 0 auto\"></div>"
HTML_SCRIPT_HIGHCHARTS_TEAM_BATTLE_PROGRESS_DIV_TAG_TEAM2 = "<div id=\"team_progress2\" style=\"min-width: 310px; height: 400px; margin: 0 auto\"></div>"

HTML_SCRIPT_HIGHCHARTS_TEAM_BATTLE_PROGRESS_DIV_TAG = \
  "      <table style=\"width: 100%;\">\n" \
  "        <tr>\n" \
  "          <td style=\"width: 50%\">\n" \
  "            <div id=\"team_progress1\" style=\"height: 400px; margin: 0 auto\"></div>\n" \
  "          </td>\n" \
  "          <td style=\"width: 50%\">\n" \
  "            <div id=\"team_progress2\" style=\"height: 400px; margin: 0 auto\"></div>\n" \
  "          </td>\n" \
  "        </tr>\n" \
  "      </table>\n" \

# =========================================================================================================================================================
# data: [ ['Firefox', 45.0], ['IE', 26.8]]

HTML_SCRIPT_HIGHCHARTS_DONUT_FUNCTION_TEMPLATE = \
"$(function () {\n" \
"Highcharts.chart('CHART_NAME', {\n" \
"    chart: {\n" \
"        type: 'donut',\n" \
"        options3d: {\n" \
"            enabled: true,\n" \
"            alpha: 30,\n" \
"            beta: 0,\n" \
"            depth: 1\n" \
"        }\n" \
"    },\n" \
"    title: {\n" \
"        text: 'CHART_TITLE'\n" \
"    },\n" \
"    tooltip: {\n" \
"        pointFormat: '<b>{point.y}</b>'\n" \
"    },\n" \
"    plotOptions: {\n" \
"        pie: {\n" \
"            allowPointSelect: true,\n" \
"            cursor: 'pointer',\n" \
"            depth: 50,\n" \
"            dataLabels: {\n" \
"                enabled: true,\n" \
"                format: '{point.name}: <b>{point.y}</b>'\n" \
"            },\n" \
"            innerSize: 45\n" \
"        }\n" \
"    },\n" \
"    series: [{\n" \
"        type: 'pie',\n" \
"        data: [\n" \
"ADD_ROWS" \
"        ]\n" \
"    }]\n" \
"});\n" \
"});\n"

HTML_SCRIPT_HIGHCHARTS_EMPTY_DONUT_FUNCTION = \
"$(function () {\n" \
"Highcharts.chart('CHART_NAME', {\n" \
"    chart: {\n" \
"        type: 'donut',\n" \
"        options3d: {\n" \
"            enabled: true,\n" \
"            alpha: 30,\n" \
"            beta: 0,\n" \
"            depth: 1\n" \
"        }\n" \
"    },\n" \
"    title: {\n" \
"        text: 'CHART_TITLE'\n" \
"    },\n" \
"    tooltip: {\n" \
"        pointFormat: '<b>NO</b>'\n" \
"    },\n" \
"    plotOptions: {\n" \
"        pie: {\n" \
"            allowPointSelect: true,\n" \
"            cursor: 'pointer',\n" \
"            depth: 50,\n" \
"            dataLabels: {\n" \
"                enabled: false,\n" \
"            },\n" \
"            innerSize: 70\n" \
"        }\n" \
"    },\n" \
"    series: [{\n" \
"        type: 'pie',\n" \
"        data: [\n" \
"['NO', 1]" \
"        ]\n" \
"    }]\n" \
"});\n" \
"});\n"

# HTML_SCRIPT_HIGHCHARTS_POWER_UPS_DONUTS_DIV_TAG = \
# "      <table style=\"width: 100%;\">\n" \
# "        <tr>\n" \
# "          <td style=\"width: 25%\">\n" \
# "            <div id=\"ra_donut\" style=\"height: 250px\"></div>\n" \
# "          </td>\n" \
# "          <td style=\"width: 25%\">\n" \
# "            <div id=\"ya_donut\" style=\"height: 250px\"></div>\n" \
# "          </td>\n" \
# "          <td style=\"width: 25%\">\n" \
# "            <div id=\"ga_donut\" style=\"height: 250px\"></div>\n" \
# "          </td>\n" \
# "          <td style=\"width: 25%\">\n" \
# "            <div id=\"mh_donut\" style=\"height: 250px \"></div>\n" \
# "          </td>\n" \
# "        </tr>\n" \
# "      </table>\n" \

# HTML_SCRIPT_HIGHCHARTS_TEAM_STATS_DONUTS_DIV_TAG = \
# "      <table style=\"width: 100%;\">\n" \
# "        <tr>\n" \
# "          <td style=\"width: 20%\">\n" \
# "            <div id=\"frags_donut\" style=\"height: 250px\"></div>\n" \
# "          </td>\n" \
# "          <td style=\"width: 20%\">\n" \
# "            <div id=\"kills_donut\" style=\"height: 250px\"></div>\n" \
# "          </td>\n" \
# "          <td style=\"width: 20%\">\n" \
# "            <div id=\"deaths_donut\" style=\"height: 250px\"></div>\n" \
# "          </td>\n" \
# "          <td style=\"width: 20%\">\n" \
# "            <div id=\"suicides_donut\" style=\"height: 250px \"></div>\n" \
# "          </td>\n" \
# "          <td style=\"width: 20%\">\n" \
# "            <div id=\"teamkills_donut\" style=\"height: 250px\"></div>\n" \
# "          </td>\n" \
# "        </tr>\n" \
# "      </table>\n" \

HTML_SCRIPT_HIGHCHARTS_TEAMS_STATS_DONUTS_DIV_TAG = \
"<div class=\"wpb_text_column wpb_content_element \">\n" \
"<div class=\"wpb_wrapper\">\n" \
"  <div class=\"symple-toggle state-closed\" id=\"TeamStatsDonuts\">\n" \
"    <h2 class=\"symple-toggle-trigger \">Team stats</h3>\n " \
"    <div class=\"symple-toggle-container symple-clearfix\">\n" \
"      <table style=\"width: 100%;\">\n" \
"        <tr>\n" \
"          <td style=\"width: 25%\">\n" \
"            <div id=\"ra_donut\" style=\"height: 250px\"></div>\n" \
"          </td>\n" \
"          <td style=\"width: 25%\">\n" \
"            <div id=\"ya_donut\" style=\"height: 250px\"></div>\n" \
"          </td>\n" \
"          <td style=\"width: 25%\">\n" \
"            <div id=\"ga_donut\" style=\"height: 250px\"></div>\n" \
"          </td>\n" \
"          <td style=\"width: 25%\">\n" \
"            <div id=\"mh_donut\" style=\"height: 250px \"></div>\n" \
"          </td>\n" \
"        </tr>\n" \
"      </table>\n" \
"      <hr>\n" \
"      <table style=\"width: 100%;\">\n" \
"        <tr>\n" \
"          <td style=\"width: 20%\">\n" \
"            <div id=\"frags_donut\" style=\"height: 250px\"></div>\n" \
"          </td>\n" \
"          <td style=\"width: 20%\">\n" \
"            <div id=\"kills_donut\" style=\"height: 250px\"></div>\n" \
"          </td>\n" \
"          <td style=\"width: 20%\">\n" \
"            <div id=\"deaths_donut\" style=\"height: 250px\"></div>\n" \
"          </td>\n" \
"          <td style=\"width: 20%\">\n" \
"            <div id=\"suicides_donut\" style=\"height: 250px \"></div>\n" \
"          </td>\n" \
"          <td style=\"width: 20%\">\n" \
"            <div id=\"teamkills_donut\" style=\"height: 250px\"></div>\n" \
"          </td>\n" \
"        </tr>\n" \
"      </table>\n" \
"    </div>\n" \
"  </div>\n" \
"</div>\n" \
"</div>\n";

# =========================================================================================================================================================

HTML_SCRIPT_FOLDING_SECTION_HEADER = \
"<div class=\"wpb_text_column wpb_content_element \">\n" \
"<div class=\"wpb_wrapper\">\n" \
"  <div class=\"symple-toggle state-closed\" id=\"DIV_ID_NAME\">\n" \
"    <h2 class=\"symple-toggle-trigger \">H2_CLASS_NAME</h3>\n " \
"    <div class=\"symple-toggle-container symple-clearfix\">\n" \

HTML_SCRIPT_FOLDING_SECTION_FOOTER = \
"    </div>\n" \
"  </div>\n" \
"</div>\n" \
"</div>\n";

# =========================================================================================================================================================

# HTML_SCRIPT_HIGHCHARTS_MATCH_RESULTS_FUNCTION = \
# "$(function () {\n" \
# "Highcharts.chart('match_results', {\n" \
# "    chart: {\n" \
# "        type: 'bar'\n" \
# "    },\n" \
# "    title: {\n" \
# "        text: 'Match result'\n" \
# "    },\n" \
# "    xAxis: {\n" \
# "        categories: ['frags'],\n" \
# "        labels: {\n" \
# "            enabled: false\n" \
# "        }\n" \
# "    },\n" \
# "    yAxis: {\n" \
# "        min: 0,\n" \
# "        labels: {\n" \
# "            enabled: false\n" \
# "        }\n" \
# "    },\n" \
# "    legend: {\n" \
# "    		enabled: false\n" \
# "    },\n" \
# "    plotOptions: {\n" \
# "        series: {\n" \
# "            stacking: 'percent',\n" \
# "             dataLabels: {\n" \
# "                enabled: true,\n" \
# "                style: {\n" \
# "                    fontWeight: 'bold',\n" \
# "                    fontSize: '20px'\n" \
# "                },\n" \
# "                formatter:function() {\n" \
# "                    return this.series.name + ': ' + this.point.y;\n" \
# "                }\n" \
# "            }\n" \
# "        },\n" \
# "    },\n" \
# "    series: [{\n" \
# "        name: 'red',\n" \
# "        color: 'red',\n" \
# "        data: [50]\n" \
# "    }, {\n" \
# "        name: 'xep',\n" \
# "        color: 'blue',\n" \
# "        data: [83]\n" \
# "    }]\n" \
# "});\n" \
# "});\n"
#
# HTML_SCRIPT_HIGHCHARTS_MATCH_RESULTS_DIV_TAG = "<div id=\"match_results\" style=\"height: 200px; margin: 0 auto\"></div>"

# =========================================================================================================================================================

HTML_SCRIPT_PLAYER_POWER_UPS_BY_MINUTES_BY_PLAYERS_FUNCTION =\
    "google.charts.setOnLoadCallback(drawPLAYER_NAMEPowerUpsByMinutes);\n" \
    "function drawPLAYER_NAMEPowerUpsByMinutes() {\n" \
    "var data = google.visualization.arrayToDataTable([\n " \
    "['Minute','MH','GA','YA','RA'],\n" \
    "ADD_STATS_ROWS" \
    "]);\n" \
    "var dataTotal = google.visualization.arrayToDataTable([\n" \
    "['Minute','MH','GA','YA','RA'],\n" \
    "ADD_TOTAL_STATS_ROWS" \
    "]);\n" \
    "\n" \
    "var options = {\n" \
    "  isStacked: true,\n" \
    "  height: 300,\n" \
    "  colors: ['#660066', 'green', 'yellow', 'red'],\n" \
    "  \n" \
    "  vAxis: {minValue: 0, maxValue: MAX_VALUE},\n" \
    "  legend: { position: 'right', maxLines: 2 },\n" \
    "  title: \"PLAYER_NAME power ups by minutes\"\n" \
    "};\n" \
    "var optionsTotal = {\n" \
    "  isStacked: false,\n" \
    "  height: 300,\n" \
    "  colors: ['#660066', 'green', 'yellow', 'red'],\n" \
    "  vAxis: {minValue: 0, maxValue: TOTAL_MAX__VALUE},\n" \
    "  legend: { position: \"none\" },\n" \
    "  title: \"PLAYER_NAME total power ups\"\n" \
    "};\n" \
    "\n" \
    "var chart      = new google.visualization.ColumnChart(document.getElementById('PLAYER_NAME_power_ups_div'));\n" \
    "var chartTotal = new google.visualization.ColumnChart(document.getElementById('PLAYER_NAME_total_power_ups_div'));\n" \
    "\n" \
    "chart.draw(data, options);\n" \
    "chartTotal.draw(dataTotal, optionsTotal);\n" \
    "$(\"#PLAYER_NAME_power_ups_by_minutes\").attr(\"class\", \"symple-toggle state-closed\");\n" \
    "}\n"

HTML_PLAYER_POWER_UPS_BY_MINUTES_BY_PLAYERS_DIV_TAG = \
  "<div class=\"wpb_text_column wpb_content_element \">\n" \
  "<div class=\"wpb_wrapper\">\n" \
  "  <div class=\"symple-toggle state-open\" id=\"PLAYER_NAME_power_ups_by_minutes\">\n" \
  "    <h2 class=\"symple-toggle-trigger \">PLAYER_NAME power ups by minutes</h2>\n" \
  "    <div class=\"symple-toggle-container symple-clearfix\">\n" \
  "      <table style=\"width: 100%;\">\n" \
  "        <tr>\n" \
  "          <td style=\"width: 83%\">\n" \
  "            <div id=\"PLAYER_NAME_power_ups_div\" style=\"width:  100%; height:  300px;\"></div>\n" \
  "          </td>\n" \
  "          <td style=\"width: 17%\">\n" \
  "            <div id=\"PLAYER_NAME_total_power_ups_div\" style=\"width:  100%; height:  300px;\"></div>\n" \
  "          </td>\n" \
  "        </tr>\n" \
  "      </table>\n" \
  "    </div>\n" \
  "  </div>\n" \
  "</div>\n" \
  "</div>\n";

# =========================================================================================================================================================

HTML_PLAYERS_ACHIEVEMENTS_DIV_TAG = \
  "<div class=\"wpb_text_column wpb_content_element \">\n" \
  "<div class=\"wpb_wrapper\">\n" \
  "  <div class=\"symple-toggle state-open\" id=\"achievements\">\n" \
  "  <h2 class=\"symple-toggle-trigger \">Achievements</h2>\n" \
  "  <div class=\"symple-toggle-container symple-clearfix\" style='overflow-x:scroll;overflow-y:hidden'>\n" \
  "PLAYERS_ACHIEVEMENTS_TABLE" \
  "  </div>\n" \
  "  </div>\n" \
  "</div>\n" \
  "</div>\n"

# =========================================================================================================================================================

HTML_EXPAND_CHECKBOX_FUNCTION = \
  "function expandCollapseKillsByMinutes() {\n" \
  "$(\"h3.symple-toggle-trigger\").toggleClass(\"active\").next().slideToggle(\"fast\")\n" \
  "}\n"

HTML_EXPAND_CHECKBOX_TAG = "<input type=\"checkbox\" id=\"expandChBox\" onChange=\"expandCollapseKillsByMinutes()\"/>Expand/Collapse All\n"

# =========================================================================================================================================================

HTML_EXPAND_POWER_UPS_CHECKBOX_FUNCTION = \
  "function expandCollapsePowerUps() {\n" \
  "$(\"h2.symple-toggle-trigger\").toggleClass(\"active\").next().slideToggle(\"fast\")\n" \
  "}\n"

HTML_EXPAND_POWER_UPS_CHECKBOX_TAG = "<input type=\"checkbox\" id=\"expandPowerUpsChBox\" onChange=\"expandCollapsePowerUps()\"/>Expand/Collapse PowerUps\n"

# =========================================================================================================================================================

HTML_HEAD_FOLDING_LINKS = \
  "<link rel='stylesheet' id='symple_shortcode_styles-css'  href='symple_shortcodes_styles.css' type='text/css' media='all' />\n"

HTML_SCRIPT_SECTION_FOOTER = "</script>\n" + HTML_HEAD_FOLDING_LINKS + "</head>\n<body>\n<pre>"

HTML_FOOTER_NO_PRE = "</body>\n</html>"

HTML_PRE_CLOSE_TAG = "</pre>\n"

HTML_BODY_FOLDING_SCRIPT = \
  "<script type='text/javascript' src=\"http://seiyria.com/bootstrap-slider/dependencies/js/jquery.min.js\"></script>\n" \
  "<script type='text/javascript' src=\"http://seiyria.com/bootstrap-slider/js/bootstrap-slider.js\"></script>\n" \
  "<script src=\"https://code.highcharts.com/highcharts.js\"></script>\n" \
  "<script src=\"https://code.highcharts.com/highcharts-3d.js\"></script>\n" \
  "<script src=\"https://code.highcharts.com/modules/exporting.js\"></script>\n" \
  "<script src=\"https://code.highcharts.com/modules/accessibility.js\"></script>\n" \
  "<script src=\"https://code.highcharts.com/modules/series-label.js\"></script>\n" \
  "<script src=\"https://code.highcharts.com/modules/export-data.js\"></script>\n" \
  "<script type='text/javascript'>\n" \
  "  var timelineSliderOnChange = function() { drawAllStreakTimelines(timelineSliderObj.getValue()); console.log(timelineSliderObj.getValue()) }\n" \
  "  var timelineSliderObj = $('#timeline_slider').slider({\n" \
  "   min  : 1,\n" \
  "   max  : 25,\n" \
  "  value: 3,\n" \
  "  ticks: [1,5,10,15,20],\n" \
  "  ticks_labels: ['1','5','10','15','20'],\n" \
  "  orientation: 'vertical',\n" \
  "  tooltip_position:'left',\n" \
  "  tooltip: 'always'\n" \
  "}).on('change', timelineSliderOnChange).data('slider');\n" \
  "</script>" \
  "<script type='text/javascript'>" \
  "jQuery(function($){$(document).ready(function(){$(\"h1.symple-toggle-trigger\").click(function(){$(this).toggleClass(\"active\").next().slideToggle(\"fast\");return false;});});});\n" \
  "jQuery(function($){$(document).ready(function(){$(\"h2.symple-toggle-trigger\").click(function(){$(this).toggleClass(\"active\").next().slideToggle(\"fast\");return false;});});});\n" \
  "jQuery(function($){$(document).ready(function(){$(\"h3.symple-toggle-trigger\").click(function(){$(this).toggleClass(\"active\").next().slideToggle(\"fast\");return false;});});});\n" \
  "</script>\n"

# =========================================================================================================================================================
  
HTML_SCRIPT_HIGHCHARTS_TOTALS_FRAGS_PROGRESS_DIV_TAG = "<div id=\"highchart_totals_frags\" style=\"min-width: 310px; height: 500px; margin: 0 auto\"></div>"
  
HTML_SCRIPT_HIGHCHARTS_TOTALS_FRAGS_PROGRESS_FUNCTION = \
"$(function () {\n" \
"Highcharts.theme = {\n" \
"   chart: {\n" \
"      backgroundColor: null,\n" \
"      style: {\n" \
"         fontFamily: \"Dosis, sans-serif\"\n" \
"      }\n" \
"   },\n" \
"   title: {\n" \
"      style: {\n" \
"         fontSize: '16px',\n" \
"         fontWeight: 'bold',\n" \
"         textTransform: 'uppercase'\n" \
"      }\n" \
"   },\n" \
"   tooltip: {\n" \
"      borderWidth: 0,\n" \
"      backgroundColor: 'rgba(219,219,216,0.8)',\n" \
"      shadow: false\n" \
"   },\n" \
"   legend: {\n" \
"      itemStyle: {\n" \
"         fontWeight: 'bold',\n" \
"         fontSize: '13px'\n" \
"      }\n" \
"   },\n" \
"   xAxis: {\n" \
"      \n" \
"      gridLineWidth: 1,\n" \
"      labels: {\n" \
"         style: {\n" \
"            fontSize: '12px'\n" \
"         }\n" \
"      }\n" \
"   },\n" \
"   yAxis: {\n" \
"      title: {\n" \
"         style: {\n" \
"            textTransform: 'uppercase'\n" \
"         }\n" \
"      },\n" \
"      labels: {\n" \
"         style: {\n" \
"            fontSize: '12px'\n" \
"         }\n" \
"      },\n" \
"MIN_PLAYER_FRAGS\n" \
"MAX_PLAYER_FRAGS\n" \
"   },\n" \
"   plotOptions: {\n" \
"      candlestick: {\n" \
"         lineColor: '#404048'\n" \
"      }\n" \
"   },\n" \
"\n" \
"\n" \
"   // General\n" \
"   background2: '#F0F0EA'\n" \
"\n" \
"};\n" \
"\n" \
"// Apply the theme\n" \
"Highcharts.setOptions(Highcharts.theme);\n" \
"\n" \
"    $('#highchart_totals_frags').highcharts({\n" \
"        chart: {\n" \
"                zoomType: 'x'\n" \
"            },\n" \
"        title: {\n" \
"            text: 'GRAPH_TITLE',\n" \
"            x: -20 //center\n" \
"        },\n" \
"        subtitle: {\n" \
"            text: '',\n" \
"            x: -20\n" \
"        },\n" \
"        xAxis: {\n" \
"            title: {\n" \
"                text: 'Time'\n" \
"            },\n" \
"EXTRA_XAXIS_OPTIONS" \
"        },\n" \
"        yAxis: {\n" \
"            title: {\n" \
"                text: 'Y_AXIS_TITLE'\n" \
"            },\n" \
"            plotLines: [{\n" \
"                value: 0,\n" \
"                width: 1,\n" \
"                color: '#808080'\n" \
"            }]\n" \
"        },\n" \
"        tooltip: {\n" \
"TOOLTIP_STYLE" \
"        },\n" \
"        legend: {\n" \
"            layout: 'vertical',\n" \
"            align: 'right',\n" \
"            verticalAlign: 'middle',\n" \
"            borderWidth: 0\n" \
"        },\n" \
"        series: [{\n" \
"ADD_STAT_ROWS" \
"        }]\n" \
"    });\n" \
"});\n" \


HIGHCHARTS_TOTALS_FRAGS_PROGRESS_GRANULARITY = 1

# =========================================================================================================================================================
  
HTML_SCRIPT_HIGHCHARTS_TOTALS_AVG_FRAGS_PROGRESS_DIV_TAG = "<div id=\"highchart_totals_avg_frags\" style=\"min-width: 310px; height: 500px; margin: 0 auto\"></div>"
  
HTML_SCRIPT_HIGHCHARTS_TOTALS_AVG_FRAGS_PROGRESS_FUNCTION = \
"$(function () {\n" \
"Highcharts.theme = {\n" \
"   chart: {\n" \
"      backgroundColor: null,\n" \
"      style: {\n" \
"         fontFamily: \"Dosis, sans-serif\"\n" \
"      }\n" \
"   },\n" \
"   title: {\n" \
"      style: {\n" \
"         fontSize: '16px',\n" \
"         fontWeight: 'bold',\n" \
"         textTransform: 'uppercase'\n" \
"      }\n" \
"   },\n" \
"   tooltip: {\n" \
"      borderWidth: 0,\n" \
"      backgroundColor: 'rgba(219,219,216,0.8)',\n" \
"      shadow: false\n" \
"   },\n" \
"   legend: {\n" \
"      itemStyle: {\n" \
"         fontWeight: 'bold',\n" \
"         fontSize: '13px'\n" \
"      }\n" \
"   },\n" \
"   xAxis: {\n" \
"      \n" \
"      gridLineWidth: 1,\n" \
"      labels: {\n" \
"         style: {\n" \
"            fontSize: '12px'\n" \
"         }\n" \
"      }\n" \
"   },\n" \
"   yAxis: {\n" \
"      title: {\n" \
"         style: {\n" \
"            textTransform: 'uppercase'\n" \
"         }\n" \
"      },\n" \
"      labels: {\n" \
"         style: {\n" \
"            fontSize: '12px'\n" \
"         }\n" \
"      },\n" \
"MIN_PLAYER_FRAGS\n" \
"MAX_PLAYER_FRAGS\n" \
"   },\n" \
"   plotOptions: {\n" \
"      candlestick: {\n" \
"         lineColor: '#404048'\n" \
"      }\n" \
"   },\n" \
"\n" \
"\n" \
"   // General\n" \
"   background2: '#F0F0EA'\n" \
"\n" \
"};\n" \
"\n" \
"// Apply the theme\n" \
"Highcharts.setOptions(Highcharts.theme);\n" \
"\n" \
"    $('#highchart_totals_avg_frags').highcharts({\n" \
"        chart: {\n" \
"                zoomType: 'x'\n" \
"            },\n" \
"        title: {\n" \
"            text: 'GRAPH_TITLE',\n" \
"            x: -20 //center\n" \
"        },\n" \
"        subtitle: {\n" \
"            text: '',\n" \
"            x: -20\n" \
"        },\n" \
"        xAxis: {\n" \
"            title: {\n" \
"                text: 'Time'\n" \
"            },\n" \
"EXTRA_XAXIS_OPTIONS" \
"        },\n" \
"        yAxis: {\n" \
"            title: {\n" \
"                text: 'Y_AXIS_TITLE'\n" \
"            },\n" \
"            plotLines: [{\n" \
"                value: 0,\n" \
"                width: 1,\n" \
"                color: '#808080'\n" \
"            }]\n" \
"        },\n" \
"        tooltip: {\n" \
"TOOLTIP_STYLE" \
"        },\n" \
"        legend: {\n" \
"            layout: 'vertical',\n" \
"            align: 'right',\n" \
"            verticalAlign: 'middle',\n" \
"            borderWidth: 0\n" \
"        },\n" \
"        series: [{\n" \
"ADD_STAT_ROWS" \
"        }]\n" \
"    });\n" \
"});\n" \


HIGHCHARTS_TOTALS_AVG_FRAGS_PROGRESS_GRANULARITY = 1

# =========================================================================================================================================================

HTML_SCRIPT_HIGHCHARTS_TOTALS_RANK_PROGRESS_DIV_TAG = "<div id=\"highchart_totals_rank\" style=\"min-width: 310px; height: 500px; margin: 0 auto\"></div>"
  
HTML_SCRIPT_HIGHCHARTS_TOTALS_RANK_PROGRESS_FUNCTION = \
"$(function () {\n" \
"Highcharts.theme = {\n" \
"   chart: {\n" \
"      backgroundColor: null,\n" \
"      style: {\n" \
"         fontFamily: \"Dosis, sans-serif\"\n" \
"      }\n" \
"   },\n" \
"   title: {\n" \
"      style: {\n" \
"         fontSize: '16px',\n" \
"         fontWeight: 'bold',\n" \
"         textTransform: 'uppercase'\n" \
"      }\n" \
"   },\n" \
"   tooltip: {\n" \
"      borderWidth: 0,\n" \
"      backgroundColor: 'rgba(219,219,216,0.8)',\n" \
"      shadow: false\n" \
"   },\n" \
"   legend: {\n" \
"      itemStyle: {\n" \
"         fontWeight: 'bold',\n" \
"         fontSize: '13px'\n" \
"      }\n" \
"   },\n" \
"   xAxis: {\n" \
"      \n" \
"      gridLineWidth: 1,\n" \
"      labels: {\n" \
"         style: {\n" \
"            fontSize: '12px'\n" \
"         }\n" \
"      }\n" \
"   },\n" \
"   yAxis: {\n" \
"      title: {\n" \
"         style: {\n" \
"            textTransform: 'uppercase'\n" \
"         }\n" \
"      },\n" \
"      labels: {\n" \
"         style: {\n" \
"            fontSize: '12px'\n" \
"         }\n" \
"      },\n" \
"MIN_PLAYER_FRAGS\n" \
"MAX_PLAYER_FRAGS\n" \
"   },\n" \
"   plotOptions: {\n" \
"      candlestick: {\n" \
"         lineColor: '#404048'\n" \
"      }\n" \
"   },\n" \
"\n" \
"\n" \
"   // General\n" \
"   background2: '#F0F0EA'\n" \
"\n" \
"};\n" \
"\n" \
"// Apply the theme\n" \
"Highcharts.setOptions(Highcharts.theme);\n" \
"\n" \
"    $('#highchart_totals_rank').highcharts({\n" \
"        chart: {\n" \
"                zoomType: 'x'\n" \
"            },\n" \
"        title: {\n" \
"            text: 'GRAPH_TITLE',\n" \
"            x: -20 //center\n" \
"        },\n" \
"        subtitle: {\n" \
"            text: '',\n" \
"            x: -20\n" \
"        },\n" \
"        xAxis: {\n" \
"            title: {\n" \
"                text: 'Time'\n" \
"            },\n" \
"EXTRA_XAXIS_OPTIONS" \
"        },\n" \
"        yAxis: {\n" \
"            title: {\n" \
"                text: 'Y_AXIS_TITLE'\n" \
"            },\n" \
"            plotLines: [{\n" \
"                value: 0,\n" \
"                width: 1,\n" \
"                color: '#808080'\n" \
"            }]\n" \
"        },\n" \
"        tooltip: {\n" \
"TOOLTIP_STYLE" \
"        },\n" \
"        legend: {\n" \
"            layout: 'vertical',\n" \
"            align: 'right',\n" \
"            verticalAlign: 'middle',\n" \
"            borderWidth: 0\n" \
"        },\n" \
"        series: [{\n" \
"ADD_STAT_ROWS" \
"        }]\n" \
"    });\n" \
"});\n" \


HIGHCHARTS_TOTALS_RANK_PROGRESS_GRANULARITY = 1

# =========================================================================================================================================================

# HTML_SCRIPT_HIGHCHARTS_RL_SKILL_DIV_TAG = "<div id=\"highchart_rl_skill_PLAYERNAME\" style=\"min-width: 310px; height: 500px; margin: 0 auto\"></div>"
HTML_SCRIPT_HIGHCHARTS_RL_SKILL_DIV_AND_TABLE_TAG = \
"<div>" \
"      <table style=\"width: 100%;\">\n" \
"        <tr>\n" \
"TABLE_ROWS" \
"        </tr>\n" \
"      </table>\n" \
"</div>\n"

HTML_SCRIPT_HIGHCHARTS_RL_SKILL_TABLE_ROW = \
"          <td style=\"width: TD_WIDTH%\">\n" \
"            <div id=\"highchart_rl_skill_PLAYERNAME\" style=\"width:  100%; height:  200px;\"></div>\n" \
"          </td>\n" \

HTML_SCRIPT_HIGHCHARTS_RL_SKILL_FUNCTION_TEMPLATE = \
"$(function () {\n" \
"Highcharts.chart('highchart_rl_skill_PLAYERNAME', {\n" \
"  chart: {\n" \
"    plotBackgroundColor: null,\n" \
"    plotBorderWidth: 0,\n" \
"    plotShadow: false\n" \
"  },\n" \
"  title: {\n" \
"    text: 'CHART_TITLE',\n" \
"    align: 'center',\n" \
"    verticalAlign: 'middle',\n" \
"    y: 100\n" \
"  },\n" \
"  tooltip: {\n" \
"    pointFormat: '{point.percentage:.2f}% ({point.y})'\n" \
"  },\n" \
"  accessibility: {\n" \
"    point: {\n" \
"      valueSuffix: '%'\n" \
"    }\n" \
"  },\n" \
"  plotOptions: {\n" \
"    pie: {\n" \
"      dataLabels: {\n" \
"        enabled: true,\n" \
"        format: '{point.name}'\n" \
"      },\n" \
"      startAngle: -100,\n" \
"      endAngle: 100,\n" \
"      center: ['50%', '75%'],\n" \
"      size: '95%',\n" \
"      animation: { duration: 3000 }" \
"    }\n" \
"  },\n" \
"  series: [{\n" \
"    type: 'pie',\n" \
"    innerSize: '40%',\n" \
"    data: [\n" \
"ADD_ROWS" \
"    ]\n" \
"  }]\n" \
"});\n" \
"});\n"

# =========================================================================================================================================================
  
HTML_SCRIPT_HIGHCHARTS_PLAYER_LIFETIME_FUNCTION = \
"$(function () {\n" \
"Highcharts.theme = {\n" \
"   chart: {\n" \
"      backgroundColor: null,\n" \
"      style: {\n" \
"         fontFamily: \"Dosis, sans-serif\"\n" \
"      }\n" \
"   },\n" \
"   title: {\n" \
"      style: {\n" \
"         fontSize: '16px',\n" \
"         fontWeight: 'bold',\n" \
"      }\n" \
"   },\n" \
"   tooltip: {\n" \
"      borderWidth: 0,\n" \
"      backgroundColor: 'rgba(219,219,216,0.8)',\n" \
"      shadow: false,\n" \
"      shared: true\n" \
"   },\n" \
"   legend: {\n" \
"      itemStyle: {\n" \
"         fontWeight: 'bold',\n" \
"         fontSize: '13px'\n" \
"      }\n" \
"   },\n" \
"   xAxis: {\n" \
"      \n" \
"      gridLineWidth: 1,\n" \
"      labels: {\n" \
"         style: {\n" \
"            fontSize: '12px'\n" \
"         }\n" \
"      },\n" \
"EXTRA_XAXIS_OPTIONS" \
"   },\n" \
"   yAxis: {\n" \
"      title: {\n" \
"         style: {\n" \
"            textTransform: 'uppercase'\n" \
"         }\n" \
"      },\n" \
"      labels: {\n" \
"         style: {\n" \
"            fontSize: '12px'\n" \
"         }\n" \
"      },\n" \
"      min: -10,\n" \
"      max: 250,\n" \
"   },\n" \
"   plotOptions: {\n" \
"      candlestick: {\n" \
"         lineColor: '#404048'\n" \
"      }\n" \
"   },\n" \
"\n" \
"\n" \
"   // General\n" \
"   background2: '#F0F0EA'\n" \
"\n" \
"};\n" \
"\n" \
"// Apply the theme\n" \
"Highcharts.setOptions(Highcharts.theme);\n" \
"\n" \
"$('#highchart_player_lifetime_PLAYERNAME').highcharts({\n" \
"    chart: {\n" \
"        zoomType: 'x'\n" \
"    },\n" \
"    title: {\n" \
"        text: 'CHART_TITLE',\n" \
"        align: 'center'\n" \
"    },\n" \
"    xAxis: [{\n" \
"               title: {\n" \
"               text: 'Time'\n" \
"            },\n" \
"    plotLines: [\n" \
"DEATH_LINES" \
"    ],\n" \
"    }],\n" \
"    yAxis: [{ // Primary yAxis\n" \
"        labels: {\n" \
"            format: '{value}',\n" \
"            style: {\n" \
"                color: 'black'\n" \
"            }\n" \
"        },\n" \
"        title: {\n" \
"            text: 'Armor',\n" \
"            style: {\n" \
"                color: 'black'\n" \
"            }\n" \
"        }\n" \
"\n" \
"    }, { // Secondary yAxis\n" \
"        gridLineWidth: 0,\n" \
"        title: {\n" \
"            text: 'Health',\n" \
"            style: {\n" \
"                color: 'blue'\n" \
"            }\n" \
"        },\n" \
"        labels: {\n" \
"            format: '{value}',\n" \
"            style: {\n" \
"                color: 'blue'\n" \
"            }\n" \
"        },\n" \
"        opposite: true\n" \
"\n" \
"    }],\n" \
"    tooltip: {\n" \
"        shared: true\n" \
"    },\n" \
"    legend: {\n" \
"        layout: 'vertical',\n" \
"        align: 'left',\n" \
"        x: 180,\n" \
"        verticalAlign: 'top',\n" \
"        y: 55,\n" \
"        floating: true,\n" \
"        backgroundColor:\n" \
"            Highcharts.defaultOptions.legend.backgroundColor || // theme\n" \
"            'rgba(255,255,255,0.25)'\n" \
"    },\n" \
"    series: [ {\n" \
"        name: 'Health',\n" \
"     \n" \
"        data: [ " \
"HEALTH_ROWS" \
"],\n" \
"        marker: {\n" \
"            enabled: false\n" \
"        },\n" \
"        \n" \
"        tooltip: {\n" \
"            valueSuffix: ''\n" \
"        },\n" \
"                color: 'blue'\n" \
"\n" \
"    }, {\n" \
"        name: 'Armor',        \n" \
"        yAxis: 1,\n" \
"        data: [" \
"ARMOR_ROWS" \
"],\n" \
"        marker: {\n" \
"            enabled: false\n" \
"        },\n" \
"        tooltip: {\n" \
"            valueSuffix: ''\n" \
"        },\n" \
"                color: 'black'\n" \
"    }],\n" \
"    responsive: {\n" \
"        rules: [{\n" \
"            condition: {\n" \
"                maxWidth: 500\n" \
"            },\n" \
"            chartOptions: {\n" \
"                legend: {\n" \
"                    floating: true,\n" \
"                    layout: 'horizontal',\n" \
"                    align: 'center',\n" \
"                    verticalAlign: 'bottom',\n" \
"                    x: 0,\n" \
"                    y: 0\n" \
"                },\n" \
"                yAxis: [{\n" \
"                    labels: {\n" \
"                        align: 'right',\n" \
"                        x: 0,\n" \
"                        y: -6\n" \
"                    },\n" \
"                    showLastLabel: false\n" \
"                }, {\n" \
"                    labels: {\n" \
"                        align: 'left',\n" \
"                        x: 0,\n" \
"                        y: -6\n" \
"                    },\n" \
"                    showLastLabel: false\n" \
"                }, {\n" \
"                    visible: false\n" \
"                }]\n" \
"            }\n" \
"        }]\n" \
"    }\n" \
"});\n" \
"});\n"

# HTML_SCRIPT_HIGHCHARTS_PLAYER_LIFETIME_DIV_TAG = "<div id=\"highchart_player_lifetime_PLAYERNAME\" style=\"min-width: 310px; height: 500px; margin: 0 auto\"></div>"
HTML_SCRIPT_HIGHCHARTS_PLAYER_LIFETIME_DIV_TAG = \
"<div class=\"wpb_text_column wpb_content_element \">\n" \
  "<div class=\"wpb_wrapper\">\n" \
  "  <div class=\"symple-toggle state-closed\" id=\"highchart_player_lifetime_PLAYERNAME_folding\">\n" \
  "    <h2 class=\"symple-toggle-trigger \">Lifetime of PLAYERNAME</h3>\n " \
  "    <div class=\"symple-toggle-container symple-clearfix\">\n" \
  "       <div id=\"highchart_player_lifetime_PLAYERNAME\" style=\"min-width: 310px; height: 500px; margin: 0 auto\"></div>" \
  "    </div>\n" \
  "  </div>\n" \
  "</div>\n" \
  "</div>\n";
 
HTML_SCRIPT_HIGHCHARTS_PLAYER_LIFETIME_DEATH_LINE_TEMPLATE = "  {color: 'LINE_COLOR', width: 1, value: LINE_VALUE, label: { text: 'LINE_LABEL', verticalAlign: 'bottom', textAlign: 'right', style: { fontSize: 10, color: 'LABEL_COLOR' }} },"
  
# =========================================================================================================================================================    
  
HTML_SCRIPT_ALL_PLAYERS_RATING_TABLE_ROW = \
"<tr style=\"height:80px;text-align:center\">\n" \
"<td style=\"width:80px\">\n" \
"<img src=\"ezquakestats\img\\total_page_imgs\PARAMETERNAME_1_1_noBG.png\" alt=\"PARAMETERDESCRIPTION\" title=\"PARAMETERDESCRIPTION\" width=\"65\" height=\"65\">\n" \
"</td>\n" \
"<td style=\"width:120px;text-align:right\">\n" \
"<img src=\"ezquakestats\img\\total_page_imgs\medal1_noBG.png\" alt=\"PARAMETERDESCRIPTION\" title=\"PARAMETERDESCRIPTION\" width=\"36\" height=\"44\">\n" \
"</td>\n" \
"<td style=\"width:20px;\"></td>\n" \
"<td style=\"width:200px; text-align:left\">\n" \
"<p>GOLD_PLAYER_NAME</p>\n" \
"</td>\n" \
"<td style=\"width:120px;text-align:right\">\n" \
"<img src=\"ezquakestats\img\\total_page_imgs\medal2_noBG.png\" alt=\"PARAMETERDESCRIPTION\" title=\"PARAMETERDESCRIPTION\" width=\"36\"  height=\"44\">\n" \
"</td>\n" \
"<td style=\"width:20px;\"></td>\n" \
"<td style=\"width:200px; text-align:left\">\n" \
"<p>SILVER_PLAYER_NAME</p>\n" \
"</td>\n" \
"<td style=\"width:120px;text-align:right\">\n" \
"<img src=\"ezquakestats\img\\total_page_imgs\medal3_noBG.png\" alt=\"PARAMETERDESCRIPTION\" title=\"PARAMETERDESCRIPTION\" width=\"36\" height=\"44\">\n" \
"</td>\n" \
"<td style=\"width:20px;\"></td>\n" \
"<td style=\"width:200px; text-align:left\">\n" \
"<p>BRONZE_PLAYER_NAME</p>\n" \
"</td>\n" \
"</tr>\n"
  
  
  
BG_COLOR_GRAY  = "#bfbfbf"
BG_COLOR_LIGHT_GRAY = "#e6e6e6"
BG_COLOR_GREEN = "#00ff00"
BG_COLOR_RED   = "#ff5c33"

KILL_STREAK_MIN_VALUE  = 3
DEATH_STREAK_MIN_VALUE = 3

def escapePlayerName(s):
    tokens = ["-", "[", "]", "\\", "^", "$", "*", ".", "?", "(", ")"]
    for tkn in tokens:
        s = s.replace(tkn, "_")
    return s

def logError(line):
    # TODO add timestamp
    ferr = open(ERROR_LOG_FILE_NAME, "a")
    ferr.write(line)
    ferr.close()

def logSkipped(line):
    # TODO add timestamp
    ferr = open(SKIPED_LINES_FILE_NAME, "a")
    ferr.write(line)
    ferr.close()

def htmlBold(s):
    return "%s%s%s" % ("<b>",s,"</b>")

def htmlLink(fname, gifPath = "", linkText = "", isBreak = True):
    return "<a href=\"%s\">%s</a>%s%s" % (fname, fname if linkText == "" else linkText, gifPath, "<br>" if isBreak else "")

def checkNew(fileNew, workFilePath, pathForCheck):
    isNew = (fileNew and workFilePath == pathForCheck)
    if not isNew:
        # check modification time
        modTime = os.stat(REPORTS_FOLDER + pathForCheck).st_mtime
        modTimeDt = datetime.fromtimestamp(int(modTime))
        timeDelta = datetime.today() - modTimeDt
        if timeDelta.total_seconds() < NEW_FILE_TIME_DETECTION:
            isNew = True

    return isNew

def readLineWithCheck(f, num):
    line = f.readline()
    num += 1
    if (num > READ_LINES_LIMIT):
        logError("ERROR: too many lines, limit = %d\n" % (READ_LINES_LIMIT))
        exit(2)
    return line,num

def isMatchStart(s):
    if "The match has begun" in s:
        return True
    return False

def isMatchEnd(s):
    if "The match is over" in s:
        return True
    return False

def commonDetection(s):
    knownSkipLines = ["not enough ammo", "second", "no weapon", "Couldn't download"]

    spl = s.split(" ")

    if "boomstick" in s: #zrkn chewed on SHAROK's boomstick
        return True, spl[3].split("'")[0], spl[0], "sg"

    elif "was gibbed" in s and "rocket" in s: #rea[rbf] was gibbed by Ilya's rocket
        return True, spl[4].split("'")[0], spl[0], "rl"

    elif "was gibbed" in s and "grenade" in s: #zrkn was gibbed by ss's grenade
        return True, spl[4].split("'")[0], spl[0], "gl"

    elif "pineapple" in s: #ss eats rea[rbf]'s pineapple
        return True, spl[2].split("'")[0], spl[0], "gl"

    elif "rocket" in s and not "took" in s and not "{rockets}" in s and not "rockets at " in s: # zrkn rides EEE's rocket
        return True, spl[2].split("'")[0], spl[0], "rl"

    elif "shaft" in s and not "fakeshaft" in s: # ss accepts Onanim's shaft
        return True, spl[2].split("'")[0], spl[0], "lg"

    elif "punctured" in s: # EEE was punctured by zrkn
        return True, spl[4].split("\n")[0], spl[0], "sng"

    elif "buckshot" in s: # Onanim ate 2 loads of SHAROK's buckshot
        return True, spl[5].split("'")[0], spl[0], "ssg"

    elif "ventilated" in s: # random was ventilated by ss
        return True, spl[4].split("\n")[0], spl[0], "sng"

    elif "perforated" in s: # Onanim was perforated by ss
        return True, spl[4].split("\n")[0], spl[0], "sng"

    elif "pierced" in s: # Artem was body pierced by zrkn
        return True, spl[5].split("\n")[0], spl[0], "ng"

    elif "nailed" in s: # Ilya was nailed by ss
        return True, spl[4].split("\n")[0], spl[0], "ng"

    elif "batteries" in s: # ss drains Onanim's batteries
        return True, spl[2].split("\'s")[0], spl[0], "lg"

    elif "ax-murdered" in s: # EEE was ax-murdered by Onanim
        return True, spl[4].split("\n")[0], spl[0], "axe"

    elif "squishes" in s: # SHAROK squishes EEE
        return True, spl[0], spl[2].split("\n")[0], "other"

    else:
        isKnown = False
        for l in knownSkipLines:
            if l in s:
                isKnown = True

        if not isKnown:
            logSkipped(s)

        return False,"","",""

def suicideDetection(s):
    detectStrs = [
                  "tries to put the pin back in", \
                  "discovers blast radius", \
                  "becomes bored with life", \
                  "fell to his death", \
                  "visits the Volcano God", \
                  "turned into hot slag", \
                  "cratered", \
                  "suicides", \
                  "died", \
                  "discharges into the water", \
                  "discharges into the slime", \
                  "discharges into the lava", \
                  "can't exist on slime alone", \
                  "gulped a load of slime", \
                  "burst into flames", \
                  "heats up the water",
                 ]
    for det in detectStrs:
         if det in s:
            return True,s.split( )[0]
    return False,""

def talefragDetection(s, teammateTelefrags):
    spl = s.split(" ")

    # special case: random stomps Ilya
    if "stomps" in s:
        return True,spl[0],spl[2].split("\n")[0]

    if "telefrag" in s:  # Ilya was telefragged by zrkn || Ilya was telefragged by his teammate

        if "teammate" in s:
            teammateTelefrags.append(spl[0])

            # check whether victim is know (in new versions)
            if len(spl) == 1 + len("was telefragged by his teammate"):
                return True,"",spl[0]  # only death is increased
            else:
                return True,spl[len(spl) - 1].replace("\r\n","").replace("\r","").replace("\n",""),spl[0]
        else:
            return True,spl[4].replace("\r\n","").replace("\r","").replace("\n",""),spl[0]

    return False,"",""

def teamkillDetection(s):
    detectStrs = ["checks his glasses", \
                  "gets a frag for the other team", \
                  "loses another friend", \
                  "mows down a teammate", \
                  "was telefragged by his teammate"]
    for det in detectStrs:
         if det in s:
            spl = s.split( )

            # check whether victim is know (in new versions)
            if len(spl) == 1 + len(det.split( )):
                return True,spl[0],""
            else:
                return True,spl[0],spl[len(spl) - 1].replace("\n","")

    return False,"",""

def powerupDetection(s):
    if "picked up" in s:
        spl = s.split(" ")

        if "megahealth" in s: # NAGIBATOR picked up megahealth
            return True, spl[0], "mh"
        elif "Yellow Armor" in s: # ss picked up Yellow Armor
            return True, spl[0], "ya"
        elif "Red Armor" in s: # ss picked up Red Armor
            return True, spl[0], "ra"
        elif "Green Armor" in s: # ss picked up Green Armor
            return True, spl[0], "ga"
        else:
            logSkipped("powerupDetection: %s" % (s))

    else:
        return False,"",""

def sortPlayersBy(players, param, fieldType="attr", units = ""):
    res = ""

    if fieldType == "attr":
        sortedPlayers = sorted(players, key=attrgetter(param), reverse=True)
    else:
        sortedPlayers = sorted(players, key=methodcaller(param), reverse=True)

    valsSum = 0
    for pl in sortedPlayers:
        exec("val = pl.%s%s" % (param, "" if fieldType == "attr" else "()"))
        valsSum += val
        res +=  "%s%s(%d%s)" % ("" if res == "" else ", ", pl.name, val, units)

    return (res if param == "damageDelta" or valsSum != 0 else "")

StreakType = enum(UNKNOWN=0, KILL_STREAK=1, DEATH_STREAK=2)
class Streak:
    def __init__(self, _type = StreakType.UNKNOWN, cnt = 0, _start = 0, _end = 0, _names = ""):
        self.type  = _type
        self.count = cnt
        self.start = _start
        self.end   = _end
        self.names = _names
        self.finalName = ""

    def clear(self):
        self.count = 0
        self.start = 0
        self.end   = 0
        # del self.names[:]
        self.names = ""
        self.finalName = ""

    def toString(self):
        return "%d [%d:%d]" % (self.count, self.start, self.end)

    def duration(self):
        return (self.end - self.start)

    def parseNames(self):
        res = []
        names = self.names[:-1]
        namesSpl = names.split(",")
        i = -1
        for spl in namesSpl:
            if i == -1 or res[i][0] != spl:
                res.append([spl,1])
                i += 1
            else:
                res[i][1] += 1

        return res

    def formattedNames(self):
        res = self.parseNames()

        resStr = ""
        for el in res:
            resStr += "%s(%d), " % (el[0], el[1])
        resStr = resStr[:-2]

        return resStr

    def formattedNamesSum(self):
        res = {}
        names = self.names[:-1]
        namesSpl = names.split(",")
        for spl in namesSpl:
            if res.has_key(spl):
                res[spl] += 1
            else:
                res[spl] = 1

        sortedRes = sorted(res.items(), key=itemgetter(1), reverse=True)

        resStr = ""
        for el in sortedRes:
            resStr += "%s(%d), " % (el[0], el[1])
        resStr = resStr[:-2]

        return resStr

def createStreaksHtmlTable(sortedPlayers, streakType):
    streaksList = []  # [[name1,[s1,s2,..]]]
    maxCnt = 0
    for pl in sortedPlayers:
        strkRes,maxStrk,strkNames = pl.getCalculatedStreaks() if streakType == StreakType.KILL_STREAK else pl.getDeatchStreaks()
        streaksList.append( [pl.name, strkRes, strkNames] )
        maxCnt = max(maxCnt,len(strkRes))
        if streakType == StreakType.KILL_STREAK and maxStrk != pl.streaks:
            logError("WARNING: for players %s calculated streak(%d) is NOT equal to given streak(%d)\n" % (pl.name, maxStrk, pl.streaks))

    cellWidth = "20px"
    streaksHtmlTable = HTML.Table(border="1", cellspacing="1",
                           style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")
    for strk in streaksList:
        tableRow = HTML.TableRow(cells=[ HTML.TableCell(htmlBold(strk[0]), align="center", width=cellWidth) ])

        maxVal = 0
        if len(strk[1]) > 0:
            maxVal = sorted(strk[1], reverse=True)[0]

        i = 0
        for val in strk[1]:
            if val == maxVal:
                tableRow.cells.append( HTML.TableCell(htmlBold(str(val)),
                                                      align="center",
                                                      width=cellWidth,
                                                      bgcolor=BG_COLOR_GREEN if streakType == StreakType.KILL_STREAK else BG_COLOR_RED) )
            else:
                tableRow.cells.append( HTML.TableCell(str(val), align="center", width=cellWidth) )
            i += 1

        for j in xrange(i,maxCnt):
            tableRow.cells.append( HTML.TableCell("", width=cellWidth) )

        streaksHtmlTable.rows.append(tableRow)

    return streaksHtmlTable


def createFullStreaksHtmlTable(sortedPlayers, streakType):
    streaksList = []  # [[name1,[s1,s2,..]]]
    maxCnt = 0
    for pl in sortedPlayers:

        strkRes,maxStrk = pl.getCalculatedStreaksFull() if streakType == StreakType.KILL_STREAK else pl.getDeatchStreaksFull()
        streaksList.append( [pl.name, strkRes] )
        maxCnt = max(maxCnt,len(strkRes))
        if streakType == StreakType.KILL_STREAK and maxStrk != pl.streaks:
            logError("WARNING: for players %s calculated streak(%d) is NOT equal to given streak(%d)\n" % (pl.name, maxStrk, pl.streaks))

    cellWidth = "20px"
    streaksHtmlTable = HTML.Table(border="1", cellspacing="1",
                           style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")
    for strk in streaksList:
        tableRow = HTML.TableRow(cells=[ HTML.TableCell(htmlBold(strk[0]), align="center", width=cellWidth) ])

        maxVal = 0
        if len(strk[1]) > 0:
            maxVal = (sorted(strk[1], key=attrgetter("count"), reverse=True)[0]).count

        i = 0
        for val in strk[1]:
            if val.count == maxVal:
                tableRow.cells.append( HTML.TableCell(htmlBold(val.toString()),
                                                      align="center",
                                                      width=cellWidth,
                                                      bgcolor=BG_COLOR_GREEN if streakType == StreakType.KILL_STREAK else BG_COLOR_RED) )
            else:
                tableRow.cells.append( HTML.TableCell(val.toString(), align="center", width=cellWidth) )
            i += 1

        for j in xrange(i,maxCnt):
            tableRow.cells.append( HTML.TableCell("", width=cellWidth) )

        streaksHtmlTable.rows.append(tableRow)

    return streaksHtmlTable


PowerUpType = enum(UNKNOWN=0, RA=1, YA=2, GA=3, MH=4)
def powerUpTypeToString(pwrType):
    if pwrType == PowerUpType.RA: return "RA"
    if pwrType == PowerUpType.YA: return "YA"
    if pwrType == PowerUpType.GA: return "GA"
    if pwrType == PowerUpType.MH: return "MH"
    return "NA"

class PowerUp:
    def __init__(self, _type = PowerUpType.UNKNOWN, _time = 0, _playerName = ""):
        self.type = _type
        self.time = _time
        self.playerName = _playerName

    def __str__(self):
        return "%s [%d]" % (powerUpTypeToString(self.type), self.time)

PlayerLifetimeDeathType = enum(NONE=0, COMMON=1, SUICIDE=2, TEAM_KILL=3)
        
class PlayerLifetimeElement:
    def __init__(self, _time, _health, _armor, _deathType = PlayerLifetimeDeathType.NONE, _killer = ""):
        self.time = _time
        self.health = _health
        self.armor = _armor
        self.deathType = _deathType
        self.killer = _killer
        
    def __str__(self):
        return "time: %f, health: %d, armor: %d, deathType: %d, killer: %s" % (self.time, self.health, self.armor, self.deathType, self.killer)
        
class KillSteal:
    def __init__(self, _time, _stealer, _target, _victim, _attackers, _confidence):
        self.time = _time
        self.stealer = _stealer
        self.target = _target
        self.stealvictim = _victim
        self.attackers = _attackers
        self.confidence = _confidence
        
class Player:
    def __init__(self, teamname, name, score, origDelta, teamkills):
        self.teamname = teamname
        self.name = name
        self.origScore = score
        self.origDelta = origDelta
        self.origTeamkills = teamkills
        self.correctedDelta = 0
        self.kills = 0
        self.deaths = 0
        self.suicides = 0
        self.teamkills = 0
        self.teamdeaths = 0

        self.streaks = 0
        self.spawnfrags = 0

        self.ga = 0
        self.ya = 0
        self.ra = 0
        self.mh = 0
        self.tkn = 0
        self.gvn = 0
        self.tm  = 0

        self.rlskill_ad = 0
        self.rlskill_dh = 0

        self.w_rl = 0
        self.w_lg = 0
        self.w_gl = 0
        self.w_sg = 0
        self.w_ssg = 0

        self.rl_kills = 0
        self.lg_kills = 0
        self.gl_kills = 0
        self.sg_kills = 0
        self.ssg_kills = 0
        self.ng_kills = 0
        self.sng_kills = 0
        self.axe_kills = 0
        self.tele_kills = 0
        self.other_kills = 0
        #self.TODO_kills = 0

        self.rl_deaths = 0
        self.lg_deaths = 0
        self.gl_deaths = 0
        self.sg_deaths = 0
        self.ssg_deaths = 0
        self.ng_deaths = 0
        self.sng_deaths = 0
        self.axe_deaths = 0
        self.tele_deaths = 0
        self.other_deaths = 0
        #self.TODO_deaths = 0

        self.calculatedStreaks = []
        self.currentStreak = Streak(StreakType.KILL_STREAK)

        self.deathStreaks = []
        self.currentDeathStreak = Streak(StreakType.DEATH_STREAK)

        self.gaByMinutes = []
        self.yaByMinutes = []
        self.raByMinutes = []
        self.mhByMinutes = []

        self.powerUps = []

        self.achievements = []

        self.connectTime = 0
        self.disconnectTime = 0
        self.isDropped = False

        self.kill_weapons = set()
        self.death_weapons = set()

        # XML data
        self.damageSelf = 0
        self.damageGvn = 0
        self.damageTkn = 0
        self.damageSelfArmor = 0
        self.damageGvnArmor = 0
        self.damageTknArmor = 0
        self.killsXML = 0
        self.deathsXML = 0
        self.suicidesXML = 0
        self.spawnFragsXML = 0
        self.gaXML = 0
        self.yaXML = 0
        self.raXML = 0
        self.mhXML = 0
        self.gaByMinutesXML = []
        self.yaByMinutesXML = []
        self.raByMinutesXML = []
        self.mhByMinutesXML = []

        self.rl_damage_gvn = 0
        self.lg_damage_gvn = 0
        self.gl_damage_gvn = 0
        self.sg_damage_gvn = 0
        self.ssg_damage_gvn = 0
        self.ng_damage_gvn = 0
        self.sng_damage_gvn = 0
        self.axe_damage_gvn = 0
        self.tele_damage_gvn = 0
        self.other_damage_gvn = 0
        #self.TODO_damage_gvn = 0

        self.rl_damages_gvn = []
        self.rl_damages_tkn = []

        self.rl_damage_tkn = 0
        self.lg_damage_tkn = 0
        self.gl_damage_tkn = 0
        self.sg_damage_tkn = 0
        self.ssg_damage_tkn = 0
        self.ng_damage_tkn = 0
        self.sng_damage_tkn = 0
        self.axe_damage_tkn = 0
        self.tele_damage_tkn = 0
        self.other_damage_tkn = 0
        #self.TODO_damage_tkn = 0

        self.rl_damage_gvn_cnt = 0
        self.lg_damage_gvn_cnt = 0
        self.gl_damage_gvn_cnt = 0
        self.sg_damage_gvn_cnt = 0
        self.ssg_damage_gvn_cnt = 0
        self.ng_damage_gvn_cnt = 0
        self.sng_damage_gvn_cnt = 0
        self.axe_damage_gvn_cnt = 0
        self.tele_damage_gvn_cnt = 0
        self.other_damage_gvn_cnt = 0
        #self.TODO_damage_gvn_cnt = 0

        self.rl_damage_tkn_cnt = 0
        self.lg_damage_tkn_cnt = 0
        self.gl_damage_tkn_cnt = 0
        self.sg_damage_tkn_cnt = 0
        self.ssg_damage_tkn_cnt = 0
        self.ng_damage_tkn_cnt = 0
        self.sng_damage_tkn_cnt = 0
        self.axe_damage_tkn_cnt = 0
        self.tele_damage_tkn_cnt = 0
        self.other_damage_tkn_cnt = 0
        #self.TODO_damage_tkn_cnt = 0

        self.rl_damage_self = 0
        self.lg_damage_self = 0
        self.gl_damage_self = 0
        self.sg_damage_self = 0
        self.ssg_damage_self = 0
        self.ng_damage_self = 0
        self.sng_damage_self = 0
        self.axe_damage_self = 0
        self.tele_damage_self = 0
        self.other_damage_self = 0
        #self.TODO_damage_self = 0

        self.overtime_frags = -1
        
        self.rl_attacks = -1
        
        self.double_kills = []  # [[target1,target2,wp1],...]
        self.triple_kills = []  # [[time,target1,target2,target3,wp],...]
        self.mutual_kills = []  # [[time,target,kill_wp,death_wp],..]
        self.suicide_kills = []  # [[time,target,wp],..]
        
        self.currentHealth = 100
        self.currentArmor = 0
        self.lifetime = []
        self.lifetime.append( PlayerLifetimeElement(0,self.currentHealth,self.currentArmor) )        
        
        self.lifetimeXML = 0.0
        self.firstDeathXML = ""
        self.lastDeathXML = ""
        self.connectionTimeXML = 0
        
        self.health_15_cnt = 0
        self.health_25_cnt = 0
        
        self.pickups_items = {}
        self.pickups_weapons = {}
        
        self.killsteals_stealer = []
        self.killsteals_victim = []
        
        self.rl_dhs_selfdamage = []
        
        self.speed_max = 0
        self.speed_avg = 0
        
        self.duels = {}
        
        self.killsByMinutes = []
        self.deathsByMinutes = []
        self.suicidesByMinutes = []       

        
    def addLifetimeItem(self, element):
        if isinstance(element, DamageElement):
            if element.armor == 1:
                self.currentArmor -= element.value
            else:
                self.currentHealth -= element.value

            if self.currentArmor < 0:
                self.currentArmor = 0
            
            if self.currentHealth <= 0:
                self.currentHealth = 100
                self.currentArmor = 0
            else:
                self.lifetime.append( PlayerLifetimeElement(element.time,self.currentHealth,self.currentArmor) )
            
        if isinstance(element, PickMapItemElement):
            if element.isArmor:
                self.currentArmor += element.value
                
            elif element.isHealth:
                self.currentHealth += element.value
                
            self.lifetime.append( PlayerLifetimeElement(element.time,self.currentHealth,self.currentArmor) )
        
    def correctLifetime(self, minutesPlayed):  # remove elements with one timestamp - the last one for same time should be left
        correctedLT = []
        # print "VVVVVVVVVVV %s VVVVVVVVVVVVV" % (self.name)
        # for lt in self.lifetime:
            # print str(lt)
        for i in xrange(len(self.lifetime)):
            if i + 1 < len(self.lifetime):
                if self.lifetime[i].time == self.lifetime[i+1].time:
                    pass
                else:
                    correctedLT.append(self.lifetime[i])
            else:
                # last element
                correctedLT.append(self.lifetime[i])
                
        self.lifetime = correctedLT
        
        if self.lifetime[len(self.lifetime)-1].time != minutesPlayed*60:
            self.lifetime.append( PlayerLifetimeElement(minutesPlayed*60, self.lifetime[len(self.lifetime)-1].health, self.lifetime[len(self.lifetime)-1].armor) )
        # print "----------------------"
        # for lt in self.lifetime:
            # print str(lt)
        # print "^^^^^^^^^^^^^^^^^^^^^^^"
        
    def initPowerUpsByMinutes(self, minutesCnt):
        self.gaByMinutes = [0 for i in xrange(minutesCnt+1)]
        self.yaByMinutes = [0 for i in xrange(minutesCnt+1)]
        self.raByMinutes = [0 for i in xrange(minutesCnt+1)]
        self.mhByMinutes = [0 for i in xrange(minutesCnt+1)]

    def initPowerUpsByMinutesXML(self, minutesCnt):
        self.gaByMinutesXML = [0 for i in xrange(minutesCnt+1)]
        self.yaByMinutesXML = [0 for i in xrange(minutesCnt+1)]
        self.raByMinutesXML = [0 for i in xrange(minutesCnt+1)]
        self.mhByMinutesXML = [0 for i in xrange(minutesCnt+1)]
        
    def initEventsByMinutes(self, minutesCnt):
        self.killsByMinutes    = [0 for i in xrange(minutesCnt+1)]
        self.deathsByMinutes   = [0 for i in xrange(minutesCnt+1)]
        self.suicidesByMinutes = [0 for i in xrange(minutesCnt+1)]
        
    def incga(self, minuteNum, time = 0):
        self.gaByMinutes[minuteNum] += 1
        if time != 0:
            self.powerUps.append( PowerUp(PowerUpType.GA, time, self.name) )

    def incya(self, minuteNum, time = 0):
        self.yaByMinutes[minuteNum] += 1
        if time != 0:
            self.powerUps.append( PowerUp(PowerUpType.YA, time, self.name) )

    def incra(self, minuteNum, time = 0):
        self.raByMinutes[minuteNum] += 1
        if time != 0:
            self.powerUps.append( PowerUp(PowerUpType.RA, time, self.name) )

    def incmh(self, minuteNum, time = 0):
        self.mhByMinutes[minuteNum] += 1
        if time != 0:
            self.powerUps.append( PowerUp(PowerUpType.MH, time, self.name) )

    def incgaXML(self, time):
        minuteNum = int(time/60) + 1 if time%60 != 0 else 0

        self.gaByMinutesXML[minuteNum] += 1
        if time != 0:
            self.powerUps.append( PowerUp(PowerUpType.GA, time, self.name) )

    def incyaXML(self, time):
        minuteNum = int(time/60) + 1 if time%60 != 0 else 0
    
        self.yaByMinutesXML[minuteNum] += 1
        if time != 0:
            self.powerUps.append( PowerUp(PowerUpType.YA, time, self.name) )

    def incraXML(self, time):
        minuteNum = int(time/60) + 1 if time%60 != 0 else 0
        
        self.raByMinutesXML[minuteNum] += 1
        if time != 0:
            self.powerUps.append( PowerUp(PowerUpType.RA, time, self.name) )

    def incmhXML(self, time):
        minuteNum = int(time/60) + 1 if time%60 != 0 else 0

        self.mhByMinutesXML[minuteNum] += 1
        if time != 0:
            self.powerUps.append( PowerUp(PowerUpType.MH, time, self.name) )
                        
    def playTime(self):
        playTime = 0
        minutesCnt = len(self.gaByMinutes)  # TODO get minutes count
        if minutesCnt != 0:
            if self.disconnectTime != 0:
                playTime = self.disconnectTime - self.connectTime
            else:
                playTime = (minutesCnt * 60) - self.connectTime
        return playTime
        
    def playTimeXML(self):
        playTime = 0
        minutesCnt = len(self.gaByMinutes)  # TODO get minutes count
        if minutesCnt != 0 and len(self.lifetime) > 2:
            lastActionTime = self.lifetime[len(self.lifetime)-2].time  # last lifetime element is added in correctLifetime method 
            playTime = self.lifetimeXML + (lastActionTime - self.lastDeathXML.time)
        return playTime

    def recoverArmorStats(self):
        if self.ga == 0 and self.ya == 0 and self.ra == 0 and self.mh == 0 and self.isDropped:
            for ga in self.gaByMinutes:
                self.ga += ga
            for ya in self.yaByMinutes:
                self.ya += ya
            for ra in self.raByMinutes:
                self.ra += ra
            for mh in self.mhByMinutes:
                self.mh += mh

    def fillStreaks(self, time):
        if self.currentStreak.count != 0:
            if self.isDropped and \
               self.disconnectTime != 0 and \
               self.disconnectTime > self.currentStreak.start and \
               self.disconnectTime < time:
                self.currentStreak.end = self.disconnectTime
            else:
                self.currentStreak.end = time
            # self.calculatedStreaks.append(self.currentStreak)
            self.calculatedStreaks.append( Streak(StreakType.KILL_STREAK, self.currentStreak.count, self.currentStreak.start, self.currentStreak.end, self.currentStreak.names) )
            self.currentStreak.clear()

    def fillDeathStreaks(self, time):
        if self.currentDeathStreak.count != 0:
            if self.isDropped and \
               self.disconnectTime != 0 and \
               self.disconnectTime > self.currentDeathStreak.start and \
               self.disconnectTime < time:
                self.currentDeathStreak.end = self.disconnectTime
            else:
                self.currentDeathStreak.end = time
            # self.deathStreaks.append(self.currentDeathStreak)
            self.deathStreaks.append( Streak(StreakType.DEATH_STREAK, self.currentDeathStreak.count, self.currentDeathStreak.start, self.currentDeathStreak.end, self.currentDeathStreak.names) )
            self.currentDeathStreak.clear()

    def incKill(self, time, who, whom):
        self.kills += 1
        self.currentStreak.count += 1

        # self.currentStreak.names.append(whom)
        self.currentStreak.names += "%s," % (whom)

        if self.currentStreak.start == 0: self.currentStreak.start = time
        self.fillDeathStreaks(time)
        
        currentMin = int(time / 60)+1
        if currentMin >= len(self.killsByMinutes):
            currentMin = len(self.killsByMinutes)-1
        self.killsByMinutes[currentMin] += 1

    def incDeath(self, time, who, whom):
        self.deaths += 1
        self.currentDeathStreak.count += 1

        # self.currentDeathStreak.names.append(who)
        self.currentDeathStreak.names += "%s," % (who)

        if self.currentDeathStreak.start == 0: self.currentDeathStreak.start = time
        self.fillStreaks(time)
        
        self.lifetime.append( PlayerLifetimeElement(time,-1,-1,PlayerLifetimeDeathType.COMMON, who) )
        self.lifetime.append( PlayerLifetimeElement(time + 0.0001,100,0) )
        self.currentHealth = 100
        self.currentArmor = 0
        
        currentMin = int(time / 60)+1
        if currentMin >= len(self.deathsByMinutes):
            currentMin = len(self.deathsByMinutes)-1
            
        self.deathsByMinutes[currentMin] += 1

    def incSuicides(self, time):
        self.suicides += 1
        self.currentDeathStreak.count += 1

        # self.currentDeathStreak.names.append("SELF")
        self.currentDeathStreak.names += "SELF,"

        if self.currentDeathStreak.start == 0: self.currentDeathStreak.start = time
        self.fillStreaks(time)
        
        self.lifetime.append( PlayerLifetimeElement(time,-1,-1,PlayerLifetimeDeathType.SUICIDE, "SELF") )
        self.lifetime.append( PlayerLifetimeElement(time + 0.0001,100,0) )
        self.currentHealth = 100
        self.currentArmor = 0
        
        currentMin = int(time / 60)+1
        if currentMin >= len(self.suicidesByMinutes):
            currentMin = len(self.suicidesByMinutes)-1
        self.suicidesByMinutes[currentMin] += 1

    def incTeamkill(self, time, who, whom):
        self.teamkills += 1
        self.currentDeathStreak.count += 1

        self.currentDeathStreak.names += "[MATE kill]%s," % (whom)

        if self.currentDeathStreak.start == 0: self.currentDeathStreak.start = time
        self.fillStreaks(time)

    def incTeamdeath(self, time, who, whom):
        self.teamdeaths += 1
        self.currentDeathStreak.count += 1

        self.currentDeathStreak.names += "[killed by MATE]%s," % (who)

        if self.currentDeathStreak.start == 0: self.currentDeathStreak.start = time
        self.fillStreaks(time)
        
        self.lifetime.append( PlayerLifetimeElement(time,-1,-1,PlayerLifetimeDeathType.TEAM_KILL, "[MATE]%s" % (who)) )
        self.lifetime.append( PlayerLifetimeElement(time + 0.0001,100,0) )
        self.currentHealth = 100
        self.currentArmor = 0

    def frags(self):
        return (self.kills - self.teamkills - self.suicides);

    def deathsFromTeammates(self):
        return (self.origScore - self.deaths - self.suicides- self.origDelta);

    def killRatio(self): # Kill Ratio: Frags / ( Deaths + Suicides ).
        denominator = float(self.deaths + self.suicides + self.teamkills);
        return 0.0 if (denominator == 0) else (float(self.kills) / denominator)

    def efficiency(self): # Efficiency: Frags / ( Frags + Deaths + Suicides ).
        denominator = float(self.kills + self.deaths + self.suicides + self.teamkills)
        return 0.0 if (denominator == 0) else (float(self.kills) / denominator) * 100

    def damageDelta(self):
        return (self.gvn - self.tkn)

    def calcDelta(self):
        return (self.frags() - self.deaths)

    def getCalculatedStreaks(self, minCnt = KILL_STREAK_MIN_VALUE):
        maxStreak = 0
        res = []
        resNames = []
        for strk in self.calculatedStreaks:
            if strk.count >= minCnt:
                res.append(strk.count)
                resNames.append(strk.names)
                maxStreak = max(maxStreak, strk.count)

        return res, maxStreak, resNames

    def getCalculatedStreaksFull(self, minCnt = KILL_STREAK_MIN_VALUE):
        maxStreak = 0
        res = []
        for strk in self.calculatedStreaks:
            if strk.count >= minCnt:
                res.append(strk)
                maxStreak = max(maxStreak, strk.count)

        return res, maxStreak

    def getDeatchStreaks(self, minCnt = DEATH_STREAK_MIN_VALUE):
        maxStreak = 0
        res = []
        resNames = []
        for strk in self.deathStreaks:
            if strk.count >= minCnt:
                res.append(strk.count)
                resNames.append(strk.names)
                maxStreak = max(maxStreak, strk.count)

        return res, maxStreak, resNames

    def getDeatchStreaksFull(self, minCnt = DEATH_STREAK_MIN_VALUE):
        maxStreak = 0
        res = []
        for strk in self.deathStreaks:
            if strk.count >= minCnt:
                res.append(strk)
                maxStreak = max(maxStreak, strk.count)

        return res, maxStreak

    def getCalculatedStreaksStr(self, minCnt = KILL_STREAK_MIN_VALUE):
        s = ""
        res,cnt = self.getCalculatedStreaks(minCnt)
        for val in res:
            s += "{0:3d} ".format(val)
        return res, cnt

    def toString(self):
        return "[%s] %s: %d (%d) %d : kills:%d, deaths:%d, suicides:%d, teamkills:%d, delta:%d" % (self.teamname, self.name, self.origScore, self.origDelta, self.origTeamkills, self.kills, self.deaths, self.suicides, self.teamkills, self.calcDelta())

    def getFormatedStats(self):
        return "frags:{0:3d}, kills:{1:3d}, deaths:{2:3d}, suicides:{3:3d}, teamkills:{4:3d}, teamdeaths:{5:3d}, gvn-tkn: {6:5d} - {7:5d} ({8:5d}), ratio:{9:6.3}, eff:{10:6.4}%".format(self.frags(), self.kills, self.deaths, self.suicides, self.teamkills, self.teamdeaths, self.gvn, self.tkn, self.damageDelta(), self.killRatio(), self.efficiency())

    def getFormatedStats_noTeamKills(self):
        return "frags:{0:3d}, kills:{1:3d}, deaths:{2:3d}, suicides:{3:3d}, gvn-tkn: {4:5d} - {5:5d} ({6:5d}), ratio:{7:6.3}, eff:{8:6.4}%".format(self.frags(), self.kills, self.deaths, self.suicides, self.gvn, self.tkn, self.damageDelta(), self.killRatio(), self.efficiency())

    def getFormatedPowerUpsStats(self):
        return "ra:{0:2d}, ya:{1:2d}, ga:{2:2d}, mh:{3:2d}".format(self.ra, self.ya, self.ga, self.mh)

    def getWeaponsKills(self, totalValue = 0):
        if totalValue == 0:
            return "rl:{0:3d}, lg:{1:3d}, gl:{2:3d}, sg:{3:3d}, ssg:{4:3d}, ng:{5:3d}, sng:{6:3d}, tele:{7:3d}".format(self.rl_kills, self.lg_kills, self.gl_kills, self.sg_kills, self.ssg_kills, self.ng_kills, self.sng_kills, self.tele_kills)
        else:
            return "rl:{0:3d}({1:5.4}%), lg:{2:3d}({3:6.3}%), gl:{4:3d}({5:6.3}%), sg:{6:3d}({7:6.3}%), ssg:{8:3d}({9:6.3}%), ng:{10:3d}({11:6.3}%), sng:{12:3d}({13:6.3}%), tele:{14:3d}({15:6.3}%)".format( \
                                                                                                                                                             self.rl_kills, \
                                                                                                                                                             (float(self.rl_kills) / float(totalValue) * 100), \
                                                                                                                                                             self.lg_kills, \
                                                                                                                                                             (float(self.lg_kills) / float(totalValue) * 100), \
                                                                                                                                                             self.gl_kills, \
                                                                                                                                                             (float(self.gl_kills) / float(totalValue) * 100), \
                                                                                                                                                             self.sg_kills, \
                                                                                                                                                             (float(self.sg_kills) / float(totalValue) * 100), \
                                                                                                                                                             self.ssg_kills, \
                                                                                                                                                             (float(self.ssg_kills) / float(totalValue) * 100), \
                                                                                                                                                             self.ng_kills,  # 10 \
                                                                                                                                                             (float(self.ng_kills) / float(totalValue) * 100), \
                                                                                                                                                             self.sng_kills, \
                                                                                                                                                             (float(self.sng_kills) / float(totalValue) * 100), \
                                                                                                                                                             self.tele_kills, \
                                                                                                                                                             (float(self.tele_kills) / float(totalValue) * 100))

    def getWeaponsKills(self, totalValue, weaponsCheck):
        rlstr   = "" if not weaponsCheck.is_rl    or totalValue == 0 else "rl:{0:3d}({1:5.4}%), ".format(  self.rl_kills,   (float(self.rl_kills)   / float(totalValue) * 100));
        lgstr   = "" if not weaponsCheck.is_lg    or totalValue == 0 else "lg:{0:3d}({1:6.3}%), ".format(  self.lg_kills,   (float(self.lg_kills)   / float(totalValue) * 100));
        glstr   = "" if not weaponsCheck.is_gl    or totalValue == 0 else "gl:{0:3d}({1:6.3}%), ".format(  self.gl_kills,   (float(self.gl_kills)   / float(totalValue) * 100));
        sgstr   = "" if not weaponsCheck.is_sg    or totalValue == 0 else "sg:{0:3d}({1:6.3}%), ".format(  self.sg_kills,   (float(self.sg_kills)   / float(totalValue) * 100));
        ssgstr  = "" if not weaponsCheck.is_ssg   or totalValue == 0 else "ssg:{0:3d}({1:6.3}%), ".format( self.ssg_kills,  (float(self.ssg_kills)  / float(totalValue) * 100));
        ngstr   = "" if not weaponsCheck.is_ng    or totalValue == 0 else "ng:{0:3d}({1:6.3}%), ".format(  self.ng_kills,   (float(self.ng_kills)   / float(totalValue) * 100));
        sngstr  = "" if not weaponsCheck.is_sng   or totalValue == 0 else "sng:{0:3d}({1:6.3}%), ".format( self.sng_kills,  (float(self.sng_kills)  / float(totalValue) * 100));
        axestr  = "" if not weaponsCheck.is_axe   or totalValue == 0 else "axe:{0:3d}({1:6.3}%), ".format( self.axe_kills,  (float(self.axe_kills)  / float(totalValue) * 100));
        telestr = "" if not weaponsCheck.is_tele  or totalValue == 0 else "tele:{0:3d}({1:6.3}%), ".format(self.tele_kills, (float(self.tele_kills) / float(totalValue) * 100));
        otherstr= "" if not weaponsCheck.is_other or totalValue == 0 else "other:{0:3d}({1:6.3}%), ".format( self.other_kills,  (float(self.other_kills)  / float(totalValue) * 100));

        resstr = "%s%s%s%s%s%s%s%s%s%s" % (rlstr, lgstr, glstr, sgstr, ssgstr, ngstr, sngstr, axestr, telestr, otherstr);
        if len(resstr) > 2:
            resstr = resstr[:-2]
        return resstr

    def getWeaponsDamageGvn(self, totalValue, weaponsCheck):
        rlstr   = "" if not weaponsCheck.is_rl    or totalValue == 0 else "rl:{0:4d}({1:5.4}%), ".format(  self.rl_damage_gvn,   (float(self.rl_damage_gvn)   / float(totalValue) * 100));
        lgstr   = "" if not weaponsCheck.is_lg    or totalValue == 0 else "lg:{0:4d}({1:6.3}%), ".format(  self.lg_damage_gvn,   (float(self.lg_damage_gvn)   / float(totalValue) * 100));
        glstr   = "" if not weaponsCheck.is_gl    or totalValue == 0 else "gl:{0:4d}({1:6.3}%), ".format(  self.gl_damage_gvn,   (float(self.gl_damage_gvn)   / float(totalValue) * 100));
        sgstr   = "" if not weaponsCheck.is_sg    or totalValue == 0 else "sg:{0:4d}({1:6.3}%), ".format(  self.sg_damage_gvn,   (float(self.sg_damage_gvn)   / float(totalValue) * 100));
        ssgstr  = "" if not weaponsCheck.is_ssg   or totalValue == 0 else "ssg:{0:4d}({1:6.3}%), ".format( self.ssg_damage_gvn,  (float(self.ssg_damage_gvn)  / float(totalValue) * 100));
        ngstr   = "" if not weaponsCheck.is_ng    or totalValue == 0 else "ng:{0:4d}({1:6.3}%), ".format(  self.ng_damage_gvn,   (float(self.ng_damage_gvn)   / float(totalValue) * 100));
        sngstr  = "" if not weaponsCheck.is_sng   or totalValue == 0 else "sng:{0:4d}({1:6.3}%), ".format( self.sng_damage_gvn,  (float(self.sng_damage_gvn)  / float(totalValue) * 100));
        axestr  = "" if not weaponsCheck.is_axe   or totalValue == 0 else "axe:{0:4d}({1:6.3}%), ".format( self.axe_damage_gvn,  (float(self.axe_damage_gvn)  / float(totalValue) * 100));
        telestr = "" if not weaponsCheck.is_tele  or totalValue == 0 else "tele:{0:4d}({1:6.3}%), ".format(self.tele_damage_gvn, (float(self.tele_damage_gvn) / float(totalValue) * 100));
        otherstr= "" if not weaponsCheck.is_other or totalValue == 0 else "other:{0:4d}({1:6.3}%), ".format( self.other_damage_gvn,  (float(self.other_damage_gvn)  / float(totalValue) * 100));

        resstr = "%s%s%s%s%s%s%s%s%s%s" % (rlstr, lgstr, glstr, sgstr, ssgstr, ngstr, sngstr, axestr, telestr, otherstr);
        if len(resstr) > 2:
            resstr = resstr[:-2]
        return resstr        
        
    def getWeaponsDeaths(self, totalValue = 0):
        if totalValue == 0:
            return "rl:{0:3d}, lg:{1:3d}, gl:{2:3d}, sg:{3:3d}, ssg:{4:3d}, ng:{5:3d}, sng:{6:3d}, tele:{7:3d}".format(self.rl_deaths, self.lg_deaths, self.gl_deaths, self.sg_deaths, self.ssg_deaths, self.ng_deaths, self.sng_deaths, self.tele_deaths)
        else:
            return "rl:{0:3d}({1:5.4}%), lg:{2:3d}({3:6.3}%), gl:{4:3d}({5:6.3}%), sg:{6:3d}({7:6.3}%), ssg:{8:3d}({9:6.3}%), ng:{10:3d}({11:6.3}%), sng:{12:3d}({13:6.3}%), tele:{14:3d}({15:6.3}%)".format( \
                                                                                                                                                             self.rl_deaths, \
                                                                                                                                                             (float(self.rl_deaths) / float(totalValue) * 100), \
                                                                                                                                                             self.lg_deaths, \
                                                                                                                                                             (float(self.lg_deaths) / float(totalValue) * 100), \
                                                                                                                                                             self.gl_deaths, \
                                                                                                                                                             (float(self.gl_deaths) / float(totalValue) * 100), \
                                                                                                                                                             self.sg_deaths, \
                                                                                                                                                             (float(self.sg_deaths) / float(totalValue) * 100), \
                                                                                                                                                             self.ssg_deaths, \
                                                                                                                                                             (float(self.ssg_deaths) / float(totalValue) * 100), \
                                                                                                                                                             self.ng_deaths,  # 10 \
                                                                                                                                                             (float(self.ng_deaths) / float(totalValue) * 100), \
                                                                                                                                                             self.sng_deaths, \
                                                                                                                                                             (float(self.sng_deaths) / float(totalValue) * 100), \
                                                                                                                                                             self.tele_deaths, \
                                                                                                                                                             (float(self.tele_deaths) / float(totalValue) * 100))

    def getWeaponsDeaths(self, totalValue, weaponsCheck):
        rlstr   = "" if not weaponsCheck.is_rl    or totalValue == 0 else "rl:{0:3d}({1:5.4}%), ".format(  self.rl_deaths,   (float(self.rl_deaths)   / float(totalValue) * 100));
        lgstr   = "" if not weaponsCheck.is_lg    or totalValue == 0 else "lg:{0:3d}({1:6.3}%), ".format(  self.lg_deaths,   (float(self.lg_deaths)   / float(totalValue) * 100));
        glstr   = "" if not weaponsCheck.is_gl    or totalValue == 0 else "gl:{0:3d}({1:6.3}%), ".format(  self.gl_deaths,   (float(self.gl_deaths)   / float(totalValue) * 100));
        sgstr   = "" if not weaponsCheck.is_sg    or totalValue == 0 else "sg:{0:3d}({1:6.3}%), ".format(  self.sg_deaths,   (float(self.sg_deaths)   / float(totalValue) * 100));
        ssgstr  = "" if not weaponsCheck.is_ssg   or totalValue == 0 else "ssg:{0:3d}({1:6.3}%), ".format( self.ssg_deaths,  (float(self.ssg_deaths)  / float(totalValue) * 100));
        ngstr   = "" if not weaponsCheck.is_ng    or totalValue == 0 else "ng:{0:3d}({1:6.3}%), ".format(  self.ng_deaths,   (float(self.ng_deaths)   / float(totalValue) * 100));
        sngstr  = "" if not weaponsCheck.is_sng   or totalValue == 0 else "sng:{0:3d}({1:6.3}%), ".format( self.sng_deaths,  (float(self.sng_deaths)  / float(totalValue) * 100));
        axestr  = "" if not weaponsCheck.is_axe   or totalValue == 0 else "axe:{0:3d}({1:6.3}%), ".format( self.axe_deaths,  (float(self.axe_deaths)  / float(totalValue) * 100));
        telestr = "" if not weaponsCheck.is_tele  or totalValue == 0 else "tele:{0:3d}({1:6.3}%), ".format(self.tele_deaths, (float(self.tele_deaths) / float(totalValue) * 100));
        otherstr= "" if not weaponsCheck.is_other or totalValue == 0 else "other:{0:3d}({1:6.3}%), ".format( self.other_deaths,  (float(self.other_deaths)  / float(totalValue) * 100));

        resstr = "%s%s%s%s%s%s%s%s%s%s" % (rlstr, lgstr, glstr, sgstr, ssgstr, ngstr, sngstr, axestr, telestr, otherstr);
        if len(resstr) > 2:
            resstr = resstr[:-2]
        return resstr

    def getWeaponsDamageTkn(self, totalValue, weaponsCheck):
        rlstr   = "" if not weaponsCheck.is_rl    or totalValue == 0 else "rl:{0:4d}({1:5.4}%), ".format(  self.rl_damage_tkn,   (float(self.rl_damage_tkn)   / float(totalValue) * 100));
        lgstr   = "" if not weaponsCheck.is_lg    or totalValue == 0 else "lg:{0:4d}({1:6.3}%), ".format(  self.lg_damage_tkn,   (float(self.lg_damage_tkn)   / float(totalValue) * 100));
        glstr   = "" if not weaponsCheck.is_gl    or totalValue == 0 else "gl:{0:4d}({1:6.3}%), ".format(  self.gl_damage_tkn,   (float(self.gl_damage_tkn)   / float(totalValue) * 100));
        sgstr   = "" if not weaponsCheck.is_sg    or totalValue == 0 else "sg:{0:4d}({1:6.3}%), ".format(  self.sg_damage_tkn,   (float(self.sg_damage_tkn)   / float(totalValue) * 100));
        ssgstr  = "" if not weaponsCheck.is_ssg   or totalValue == 0 else "ssg:{0:4d}({1:6.3}%), ".format( self.ssg_damage_tkn,  (float(self.ssg_damage_tkn)  / float(totalValue) * 100));
        ngstr   = "" if not weaponsCheck.is_ng    or totalValue == 0 else "ng:{0:4d}({1:6.3}%), ".format(  self.ng_damage_tkn,   (float(self.ng_damage_tkn)   / float(totalValue) * 100));
        sngstr  = "" if not weaponsCheck.is_sng   or totalValue == 0 else "sng:{0:4d}({1:6.3}%), ".format( self.sng_damage_tkn,  (float(self.sng_damage_tkn)  / float(totalValue) * 100));
        axestr  = "" if not weaponsCheck.is_axe   or totalValue == 0 else "axe:{0:4d}({1:6.3}%), ".format( self.axe_damage_tkn,  (float(self.axe_damage_tkn)  / float(totalValue) * 100));
        telestr = "" if not weaponsCheck.is_tele  or totalValue == 0 else "tele:{0:4d}({1:6.3}%), ".format(self.tele_damage_tkn, (float(self.tele_damage_tkn) / float(totalValue) * 100));
        otherstr= "" if not weaponsCheck.is_other or totalValue == 0 else "other:{0:4d}({1:6.3}%), ".format( self.other_damage_tkn,  (float(self.other_damage_tkn)  / float(totalValue) * 100));

        resstr = "%s%s%s%s%s%s%s%s%s%s" % (rlstr, lgstr, glstr, sgstr, ssgstr, ngstr, sngstr, axestr, telestr, otherstr);
        if len(resstr) > 2:
            resstr = resstr[:-2]
        return resstr

    def getWeaponsDamageSelf(self, totalValue, weaponsCheck):
        rlstr   = "" if not weaponsCheck.is_rl    or totalValue == 0 else "rl:{0:4d}({1:5.4}%), ".format(  self.rl_damage_self,   (float(self.rl_damage_self)   / float(totalValue) * 100));
        lgstr   = "" if not weaponsCheck.is_lg    or totalValue == 0 else "lg:{0:4d}({1:6.3}%), ".format(  self.lg_damage_self,   (float(self.lg_damage_self)   / float(totalValue) * 100));
        glstr   = "" if not weaponsCheck.is_gl    or totalValue == 0 else "gl:{0:4d}({1:6.3}%), ".format(  self.gl_damage_self,   (float(self.gl_damage_self)   / float(totalValue) * 100));
        sgstr   = "" if not weaponsCheck.is_sg    or totalValue == 0 else "sg:{0:4d}({1:6.3}%), ".format(  self.sg_damage_self,   (float(self.sg_damage_self)   / float(totalValue) * 100));
        ssgstr  = "" if not weaponsCheck.is_ssg   or totalValue == 0 else "ssg:{0:4d}({1:6.3}%), ".format( self.ssg_damage_self,  (float(self.ssg_damage_self)  / float(totalValue) * 100));
        ngstr   = "" if not weaponsCheck.is_ng    or totalValue == 0 else "ng:{0:4d}({1:6.3}%), ".format(  self.ng_damage_self,   (float(self.ng_damage_self)   / float(totalValue) * 100));
        sngstr  = "" if not weaponsCheck.is_sng   or totalValue == 0 else "sng:{0:4d}({1:6.3}%), ".format( self.sng_damage_self,  (float(self.sng_damage_self)  / float(totalValue) * 100));
        axestr  = "" if not weaponsCheck.is_axe   or totalValue == 0 else "axe:{0:4d}({1:6.3}%), ".format( self.axe_damage_self,  (float(self.axe_damage_self)  / float(totalValue) * 100));
        telestr = "" if not weaponsCheck.is_tele  or totalValue == 0 else "tele:{0:4d}({1:6.3}%), ".format(self.tele_damage_self, (float(self.tele_damage_self) / float(totalValue) * 100));
        otherstr= "" if not weaponsCheck.is_other or totalValue == 0 else "other:{0:4d}({1:6.3}%), ".format( self.other_damage_self,  (float(self.other_damage_self)  / float(totalValue) * 100));

        resstr = "%s%s%s%s%s%s%s%s%s%s" % (rlstr, lgstr, glstr, sgstr, ssgstr, ngstr, sngstr, axestr, telestr, otherstr);
        if len(resstr) > 2:
            resstr = resstr[:-2]
        return resstr

    def getWeaponsAccuracy(self, weaponsCheck):
        rlstr   = "" if not weaponsCheck.is_rl    or self.rl_damage_gvn_cnt == 0 else "rl:  {0:5.4}({1:3d}), ".format(   (float(self.rl_damage_gvn)   / float(self.rl_damage_gvn_cnt) ), self.rl_damage_gvn_cnt);
        lgstr   = "" if not weaponsCheck.is_lg    or self.lg_damage_gvn_cnt == 0 else "lg:  {0:6.3}({1:3d}), ".format(   (float(self.lg_damage_gvn)   / float(self.lg_damage_gvn_cnt) ), self.lg_damage_gvn_cnt);
        glstr   = "" if not weaponsCheck.is_gl    or self.gl_damage_gvn_cnt == 0 else "gl:  {0:6.3}({1:3d}), ".format(   (float(self.gl_damage_gvn)   / float(self.gl_damage_gvn_cnt) ), self.gl_damage_gvn_cnt);
        sgstr   = "" if not weaponsCheck.is_sg    or self.sg_damage_gvn_cnt == 0 else "sg:  {0:6.3}({1:3d}), ".format(   (float(self.sg_damage_gvn)   / float(self.sg_damage_gvn_cnt) ), self.sg_damage_gvn_cnt);
        ssgstr  = "" if not weaponsCheck.is_ssg   or self.ssg_damage_gvn_cnt == 0 else "ssg:  {0:6.3}({1:3d}), ".format(  (float(self.ssg_damage_gvn)  / float(self.ssg_damage_gvn_cnt) ), self.ssg_damage_gvn_cnt);
        ngstr   = "" if not weaponsCheck.is_ng    or self.ng_damage_gvn_cnt == 0 else "ng:  {0:6.3}({1:3d}), ".format(   (float(self.ng_damage_gvn)   / float(self.ng_damage_gvn_cnt) ), self.ng_damage_gvn_cnt);
        sngstr  = "" if not weaponsCheck.is_sng   or self.sng_damage_gvn_cnt == 0 else "sng:  {0:6.3}({1:3d}), ".format(  (float(self.sng_damage_gvn)  / float(self.sng_damage_gvn_cnt) ), self.sng_damage_gvn_cnt);
        axestr  = "" if not weaponsCheck.is_axe   or self.axe_damage_gvn_cnt == 0 else "axe:  {0:6.3}({1:3d}), ".format(  (float(self.axe_damage_gvn)  / float(self.axe_damage_gvn_cnt) ), self.axe_damage_gvn_cnt);
        telestr = "" if not weaponsCheck.is_tele  or self.tele_damage_gvn_cnt == 0 else "tele:  {0:6.3}({1:3d}), ".format( (float(self.tele_damage_gvn) / float(self.tele_damage_gvn_cnt) ), self.tele_damage_gvn_cnt);
        otherstr= "" if not weaponsCheck.is_other or self.other_damage_gvn_cnt == 0 else "other:  {0:6.3}({1:3d}), ".format( (float(self.other_damage_gvn)  / float(self.other_damage_gvn_cnt) ), self.other_damage_gvn_cnt);

        resstr = "%s%s%s%s%s%s%s%s%s%s" % (rlstr, lgstr, glstr, sgstr, ssgstr, ngstr, sngstr, axestr, telestr, otherstr);
        if len(resstr) > 2:
            resstr = resstr[:-2]
        return resstr
        
    def getWeaponsPickUps(self):
        resstr = ""
        for weapon in sorted(self.pickups_weapons, key=self.pickups_weapons.get, reverse=True):
            resstr += "%s(%d), " % (weapon, self.pickups_weapons[weapon])
        if len(resstr) > 2:
            resstr = resstr[:-2]
        return resstr
        
    def getAmmoPickUps(self):
        resstr = ""
        for ammo in sorted(self.pickups_items, key=self.pickups_items.get, reverse=True):
            resstr += "%s(%d), " % (ammo, self.pickups_items[ammo])
        if len(resstr) > 2:
            resstr = resstr[:-2]
        return resstr

    def getRLSkill(self, rl_damages):
        cnt = len(rl_damages)
        if cnt == 0:
            return "NA"

        val110 = sum(1 for val in rl_damages if val[0] == 110)
        val100 = sum(1 for val in rl_damages if val[0] >= 100)
        val90  = sum(1 for val in rl_damages if val[0] >= 90)
        val75  = sum(1 for val in rl_damages if val[0] >= 75)
        val55  = sum(1 for val in rl_damages if val[0] >= 55)

        #valmore110 = sum(1 for val in rl_damages if val[0] > 110)

        return "DirectHit110: {0:5.4}%({1:3d}),  >100: {2:5.4}%({3:3d}),  >90: {4:5.4}%({5:3d}),  >75: {6:5.4}%({7:3d}),  >55: {8:5.4}%({9:3d})    Total: {10:4d}{11}".format(
                                         ((float(val110)) / float(cnt) * 100), val110, 
                                         ((float(val100)) / float(cnt) * 100), val100, 
                                         ((float(val90))  / float(cnt) * 100), val90,
                                         ((float(val75))  / float(cnt) * 100), val75,
                                         ((float(val55))  / float(cnt) * 100), val55,
                                          cnt,
                                          "    Attacks: {0:4d}".format(self.rl_attacks) if self.rl_attacks != -1 else "")
    
    def getRLSkillGvn(self):
        return self.getRLSkill(self.rl_damages_gvn)
    
    def getRLSkillTkn(self):                                          
        return self.getRLSkill(self.rl_damages_tkn)

    def getRLSkillJSON(self):
        cnt = len(self.rl_damages_gvn)
        if cnt == 0:
            return {}

        val110 = sum(1 for val in self.rl_damages_gvn if val[0] == 110)
        val100 = sum(1 for val in self.rl_damages_gvn if val[0] < 110 and val[0] >= 100)
        val90  = sum(1 for val in self.rl_damages_gvn if val[0] < 100 and val[0] >= 90)
        val75  = sum(1 for val in self.rl_damages_gvn if val[0] < 90 and val[0] >= 75)
        val55  = sum(1 for val in self.rl_damages_gvn if val[0] < 75 and val[0] >= 55)
        val0   = sum(1 for val in self.rl_damages_gvn if val[0] < 55 and val[0] >= 0)
        
        return { "attacks"      : self.rl_attacks,
                 "damagesCount" : cnt,
                 "DH110"   : val110,
                 "100-110" : val100,
                 "90-100"  : val90,
                 "75-90"   : val75,
                 "55-75"   : val55,
                 "0-55"    : val0
               }
                
    def getDuelsJson(self):
        return self.duels

    def getStreaksJSON(self, streakType):
        res = []
        for strk in self.deathStreaks if streakType == StreakType.DEATH_STREAK else self.calculatedStreaks:
            res.append(
                { "count" : strk.count,
                  "duration" : strk.duration()
                })
        return res
        
    def getKillStreaksJSON(self):
        return self.getStreaksJSON(StreakType.KILL_STREAK)
        
    def getDeathStreaksJSON(self):
        return self.getStreaksJSON(StreakType.DEATH_STREAK)

    def getKillStealsDuelsJSON(self):
        res = {}
        for ksteal in self.killsteals_stealer:
            if self.name == ksteal.stealer:
                if ksteal.stealvictim in res.keys():
                    res[ksteal.stealvictim][0] += 1
                else:
                    res[ksteal.stealvictim] = [1,0]

        for ksteal in self.killsteals_victim:
            if self.name == ksteal.stealvictim:
                if ksteal.stealer in res.keys():
                    res[ksteal.stealer][1] += 1
                else:
                    res[ksteal.stealer] = [0,1]

        return res
        
    def correctDelta(self):
        self.correctedDelta = self.origDelta + self.suicides

    def parseWeapons(self, s): # Wp: lg14.3% rl38.5% gl4.9% sg5.8% ssg5.2%
        for weap in possibleWeapons:
            spl = s.split(weap)
            val = 0.0
            if len(spl) == 1:
                pass
            else:
                val = float(spl[1].split("%")[0])
            exec("self.w_%s = val" % (weap))

    def achievementsToString(self):
        res = ""
        for ach in self.achievements:
            res += "%s," % (ach.toString())

        if res != "":
            res = res[:-1]

        return res
        
    def getAchievementsIds(self):
        res = []
        for ach in self.achievements:
            res.append(ach.achtype)
        return res
        
    def getAchievementsJSON(self):
        res = []
        for ach in self.achievements:
            res.append({"achID" : ach.achtype})
        return res        

    # powerUpsStatus: dict: ["ra"] = True, ["ya"] = False, etc.
    def calculateAchievements(self, matchProgress, powerUpsStatus, headToHead, isTeamGame):
        connectionTime = self.connectTime if self.connectTime != 0 else self.connectionTimeXML
        # LONG_LIVE_KING
        if (len(self.deathStreaks) != 0 and self.deathStreaks[0].start >= connectionTime + 60):
            self.achievements.append( Achievement(AchievementType.LONG_LIVE_KING, "first time is killed on second %d%s" % (self.deathStreaks[0].start, "" if connectionTime == 0 else " (connected on %d sec)" % (connectionTime))) )
        else:
        # LONG_LIVE
            if (len(self.deathStreaks) != 0 and self.deathStreaks[0].start >= connectionTime + 30):
                self.achievements.append( Achievement(AchievementType.LONG_LIVE, "first time is killed on second %d%s" % (self.deathStreaks[0].start, "" if connectionTime == 0 else " (connected on %d sec)" % (connectionTime))) )

        for strk in self.deathStreaks:
            # SUICIDE_MASTER & SUICIDE_KING
            strkParsedNames = strk.parseNames()
            for el in strkParsedNames:
                if el[0] == "SELF":
                    if el[1] == 2:
                        self.achievements.append( Achievement(AchievementType.SUICIDE_MASTER, "%d suicides in a row" % (el[1])) )
                    elif el[1] >= 3:
                        self.achievements.append( Achievement(AchievementType.SUICIDE_KING, "%d suicides in a row!" % (el[1])) )

            # DEATH_STREAK_PAIN
            if strk.count >= 10:
                self.achievements.append( Achievement(AchievementType.DEATH_STREAK_PAIN, "%d deaths in a row during %d seconds" % (strk.count, strk.duration())) )

        for strk in self.calculatedStreaks:
            # KILL_STREAK
            if strk.count >= 15:
                self.achievements.append( Achievement(AchievementType.KILL_STREAK, "%d kills in a row during %d seconds" % (strk.count, strk.duration())) )
                
        # HORRIBLE_FINISH, FINISH_GURU
        if len(matchProgress) >= 2:
            pos1 = 1
            for el in matchProgress[len(matchProgress)-2]:
                if el[0] == self.name:
                    break
                else:
                    pos1 +=1

            pos2 = 1
            for el in matchProgress[len(matchProgress)-1]:
                if el[0] == self.name:
                    break
                else:
                    pos2 +=1

            if pos2 - pos1 >= 2:
                self.achievements.append( Achievement(AchievementType.HORRIBLE_FINISH, "before the last minute place was %d but finished on place %d" % (pos1, pos2)) )

            if pos2 == 1 and pos1 > 2:
                self.achievements.append( Achievement(AchievementType.FINISH_GURU, "before the last minute place was %d but won the game!!" % (pos1)) )

        # HUNDRED_KILLS
        if self.kills >= 100:
            self.achievements.append( Achievement(AchievementType.HUNDRED_KILLS, "mega killer killed %d enemies" % (self.kills)) )

        # HUNDRED_DEATHS
        if self.deaths >= 100:
            self.achievements.append( Achievement(AchievementType.HUNDRED_DEATHS, "was killed %d times" % (self.deaths)) )

        # HUNDRED_FRAGS
        if self.frags() >= 100:
            self.achievements.append( Achievement(AchievementType.HUNDRED_FRAGS, "%d frags" % (self.frags())) )

        # RED_ARMOR_EATER
        if self.ra >= 10:
            self.achievements.append( Achievement(AchievementType.RED_ARMOR_EATER, "%d red armors%s" % (self.ra, "" if self.ra < 15 else ". %d CARL!!" % (self.ra))) )

        # YELLOW_ARMOR_EATER
        if self.ya >= 10:
            self.achievements.append( Achievement(AchievementType.YELLOW_ARMOR_EATER, "%d yellow armors%s" % (self.ya, "" if self.ya < 15 else ". %d CARL!!" % (self.ya))) )

        # GREEN_ARMOR_EATER
        if self.ga >= 10:
            self.achievements.append( Achievement(AchievementType.GREEN_ARMOR_EATER, "%d green armors%s" % (self.ga, "" if self.ga < 15 else ". %d CARL!!" % (self.ga))) )

        # MEGA_HEALTH_EATER
        if self.mh >= 10:
            self.achievements.append( Achievement(AchievementType.MEGA_HEALTH_EATER, "%d mega healths%s" % (self.mh, "" if self.mh < 15 else ". %d CARL!!" % (self.mh))) )

        # RED_ARMOR_ALLERGY
        if powerUpsStatus["ra"] and self.ra == 0 and self.playTimeXML() > ((len(matchProgress) / 2) * 60):
            self.achievements.append( Achievement(AchievementType.RED_ARMOR_ALLERGY) )

        # YELLOW_ARMOR_ALLERGY
        if powerUpsStatus["ya"] and self.ya == 0 and self.playTimeXML() > ((len(matchProgress) / 2) * 60):
            self.achievements.append( Achievement(AchievementType.YELLOW_ARMOR_ALLERGY) )

        # GREEN_ARMOR_ALLERGY
        if powerUpsStatus["ga"] and self.ga == 0 and self.playTimeXML() > ((len(matchProgress) / 2) * 60):
            self.achievements.append( Achievement(AchievementType.GREEN_ARMOR_ALLERGY) )

        # MEGA_HEALTH_ALLERGY
        if powerUpsStatus["mh"] and self.mh == 0 and self.playTimeXML() > ((len(matchProgress) / 2) * 60):
            self.achievements.append( Achievement(AchievementType.MEGA_HEALTH_ALLERGY) )

        # RAINBOW_FLAG
        if self.ra >= 10 and self.ya >= 10 and self.ga >= 10:
            self.achievements.append( Achievement(AchievementType.RAINBOW_FLAG, "10+ each of armors") )

        # CHILD_KILLER
        if self.spawnfrags >= 10:
            self.achievements.append( Achievement(AchievementType.CHILD_KILLER, "%d spawn frags%s" % (self.spawnfrags, "" if self.spawnfrags < 15 else ". %d CARL!!" % (self.spawnfrags))) )

        # CHILD_LOVER
        if self.spawnfrags == 0:
            self.achievements.append( Achievement(AchievementType.CHILD_LOVER, "NO spawn frags") )
            
        # ALWAYS_THE_FIRST
        if len(matchProgress) >= 2:
            isFirst = True
            alwaysTheFirst = True
            for el in matchProgress:
                if isFirst:
                    isFirst = False
                else:
                    if not el[0][0] == self.name:
                        alwaysTheFirst = False
                        break

            if alwaysTheFirst:
                self.achievements.append( Achievement(AchievementType.ALWAYS_THE_FIRST, "the 1st place from the 1st minute until the finish") )

        # ALWAYS_THE_LAST
        if len(matchProgress) >= 2:
            if self.playTimeXML() > ((len(matchProgress)*3 / 4) * 60):
                isFirst = True
                alwaysTheLast = True
                for el in matchProgress:
                    if isFirst:
                        isFirst = False
                    else:
                        if not el[ len(el)-1 ][0] == self.name:
                            alwaysTheLast = False
                            break

                if alwaysTheLast:
                    self.achievements.append( Achievement(AchievementType.ALWAYS_THE_LAST, "the last place from the 1st minute until the finish") )

        # ROCKETS_LOVER
        if self.kills != 0 and self.kills == self.rl_kills:
            self.achievements.append( Achievement(AchievementType.ROCKETS_LOVER, "all %d kills made via rocket launcher" % (self.rl_kills)) )

        # DUEL_WINNER
        if len(matchProgress) != 0 and len(matchProgress[0]) == 2 and matchProgress[len(matchProgress)-1][0][0] == self.name:
            self.achievements.append( Achievement(AchievementType.DUEL_WINNER, "") )

        # SNIPER
        if len(self.rl_damages_gvn) != 0:
            if (sum(1 for val in self.rl_damages_gvn if val[0] == 110) / float(len(self.rl_damages_gvn)) > 0.45 and len(self.rl_damages_gvn) > 30):
                self.achievements.append( Achievement(AchievementType.SNIPER, "direct hit is {0:5.3}%".format((sum(1 for val in self.rl_damages_gvn if val[0] == 110) * 100) / float(len(self.rl_damages_gvn)))))
        else:
            if self.rlskill_dh >= 40:
                self.achievements.append( Achievement(AchievementType.SNIPER, "direct hit is %d" % (self.rlskill_dh)) )

        # PERSONAL_STALKER
        if len(matchProgress) != 0 and len(matchProgress[0]) > 3:
            sortedHeadToHead = sorted(headToHead[self.name], key=lambda x: x[1], reverse=True)
            if sortedHeadToHead[0][0] != self.name and sortedHeadToHead[0][1] > (self.kills - sortedHeadToHead[0][1]):
                self.achievements.append( Achievement(AchievementType.PERSONAL_STALKER, "killed %s %d times what more than all others taken together(%d)" % (sortedHeadToHead[0][0], sortedHeadToHead[0][1], (self.kills - sortedHeadToHead[0][1]))) )

        # SELF_DESTRUCTOR
        sortedHeadToHead = sorted(headToHead[self.name], key=lambda x: x[1], reverse=True)
        if sortedHeadToHead[0][0] == self.name:
            self.achievements.append( Achievement(AchievementType.SELF_DESTRUCTOR, "suicided %d times which more than killed any other player" % (self.suicides)) )

        # LUMBERJACK
        if self.axe_kills >= 3:
            self.achievements.append( Achievement(AchievementType.LUMBERJACK, "%d axe kills" % (self.axe_kills)) )

        # ELECTROMASTER
        if (self.kills > 0 and self.lg_kills >= 15 and ( ((float(self.lg_kills) / float(self.kills) * 100) >= 40.0) or (((float(self.lg_kills) / float(self.kills) * 100)) >= 75.0))):
            self.achievements.append( Achievement(AchievementType.ELECTROMASTER, "{0:d} lazer gun kills({1:5.3}%)".format(self.lg_kills, (float(self.lg_kills) / float(self.kills) * 100))) )

        # FASTER_THAN_BULLET
        for strk in self.calculatedStreaks:
            if strk.count >= 5 and (strk.end - strk.start > 0) and (float(strk.end - strk.start) / (float)(strk.count)) <= 3.0:
                self.achievements.append( Achievement(AchievementType.FASTER_THAN_BULLET, "streak {0:d} kills in {1:.3} seconds - only {2:.3} seconds per kill".format(strk.count, float(strk.end - strk.start), (float(strk.end - strk.start) / (float)(strk.count)))) )

        # NO_SUICIDES
        if self.playTimeXML() > ((len(matchProgress) / 2) * 60) and self.suicides == 0:
            self.achievements.append( Achievement(AchievementType.NO_SUICIDES, "") )

        # UNIVERSAL_SOLDIER
        if len(self.kill_weapons) > 5:
            self.achievements.append(Achievement(AchievementType.UNIVERSAL_SOLDIER,
                                                 'Killed with {} different weapons'.format(len(self.kill_weapons))))
        
        # MULTIPLE_PENETRATION
        if len(self.death_weapons) > 5:
            self.achievements.append(Achievement(AchievementType.MULTIPLE_PENETRATION,
                                                 'Got killed with {} different weapons'.format(len(self.death_weapons))))

        # GL_LOVER
        if self.kills > 0 and self.gl_kills >= 15 and ((float(self.gl_kills) / float(self.kills) * 100)) >= 45.0:
            self.achievements.append( Achievement(AchievementType.GL_LOVER, "{0:d} grenade launcher kills({1:5.3}%)".format(self.gl_kills, (float(self.gl_kills) / float(self.kills) * 100))) )
                                                 
        # OVERTIME
        if self.overtime_frags != -1:
            self.achievements.append( Achievement(AchievementType.OVERTIME, "goes to the overtime with {0:d} frags".format(self.overtime_frags)) )

        # COMBO_DOUBLE_KILL
        for i in xrange(len(self.double_kills)):
            self.achievements.append( Achievement(AchievementType.COMBO_DOUBLE_KILL, "killed %s and %s with one %s shot!" % (self.double_kills[i][0], self.double_kills[i][1], self.double_kills[i][2])) )
            
        # COMBO_MUTUAL_KILL
        if len(self.mutual_kills) >= 3:
            self.achievements.append( Achievement(AchievementType.COMBO_MUTUAL_KILL, "fought bravely until the last blood drop %d times" % (len(self.mutual_kills))) )
            
        # COMBO_KAMIKAZE
        if len(self.suicide_kills) >= 3:
            self.achievements.append( Achievement(AchievementType.COMBO_KAMIKAZE, "The sun on the wings - move forward! For the last time, the enemy will see the sunrise! One plane for one enemy! %d times..." % (len(self.suicide_kills))) )            
            
        # COMBO_TRIPLE_KILL
        for i in xrange(len(self.triple_kills)):
            self.achievements.append( Achievement(AchievementType.COMBO_TRIPLE_KILL, "killed %s, %s and %s with one %s shot!" % (self.triple_kills[i][1], self.triple_kills[i][2], self.triple_kills[i][3], self.triple_kills[i][4])) )
            
        if isTeamGame:
            # TEAMMATES_FAN
            if self.playTimeXML() > ((len(matchProgress) / 2) * 60) and self.teamkills == 0 and self.teamdeaths == 0:
                self.achievements.append( Achievement(AchievementType.TEAMMATES_FAN, "") )


# DO NOT FORGET TO ADD NEW ITEMS TO description() METHOD
AchievementType = enum( LONG_LIVE  = 1, #"Long Live and Prosper",  # the 1st 30 seconds without deaths                                  DONE
                        SUICIDE_MASTER = 2, # "Suicide Master",   # 2 suicides in a row                                                 DONE
                        SUICIDE_KING = 3, # "Suicide King",   # 3++ suicides in a row                                                   DONE
                        DEATH_STREAK_PAIN = 4, # "What do you know about the pain?...", # 10++ death streak                             DONE
                        GREAT_FINISH = 5, # "Great Finish", # 2+ places up during the last minute                                           #TODO
                        FINISH_GURU = 6, # "Finish Guru", # 2+ places up during the last minute and win                                 DONE
                        HORRIBLE_FINISH = 7, # "Horrible Finish - finished to play too early", # -2 places up during the last minute    DONE
                        ALWAYS_THE_FIRST = 8, # "Always the 1st", # the 1st place from the 1st minute until the finish                  DONE
                        OVERTIME = 9, # "One of who didn't want to give up", # "Overtime - extra minutes of fight" #DEATHMATCH_SPECIFIC DONE
                        SECOND_OVERTIME_REASON = 10, # "The 2nd overtime!",  # one of who didn't want to give up once more time             #TODO
                        HUNDRED_KILLS = 11, # "More than 100 kills", # 100++ kills                                                      DONE tmp img
                        HUNDRED_DEATHS = 12, # "More than 100 deaths", # 100++ deaths                                                   DONE tmp img
                        HUNDRED_FRAGS = 13, # "More than 100 frags", # 100++ frags                                                      DONE tmp img
                        RED_ARMOR_EATER = 14, # "Red armor eater", # 10+ red armors                                                     DONE
                        GREEN_ARMOR_EATER = 15, # "Green armor eater", # 10+ green armors                                               DONE
                        YELLOW_ARMOR_EATER = 16, # "Yellow armor eater", # 10+ yellow armors                                            DONE
                        MEGA_HEALTH_EATER = 17, # "Mega healths eater", # 10+ mega healths                                              DONE
                        RED_ARMOR_ALLERGY = 18, # "Red armor allergy", # No red armors                                                  DONE
                        GREEN_ARMOR_ALLERGY = 19, # "Green armor allergy", # No green armors                                            DONE
                        YELLOW_ARMOR_ALLERGY = 20, # "Yellow armor allergy", # No yellow armors                                         DONE
                        MEGA_HEALTH_ALLERGY = 21, # "Mega healths allergy", # No mega healths                                           DONE
                        CHILD_KILLER = 22, # "Child killer", # 10+ spawn frags                                                          DONE
                        ALWAYS_THE_LAST = 23, # "Always the last", # the last place from the 1st minute until the finish                DONE
                        ROCKETS_LOVER = 24, # "Rockets lover", # all kills made via rocket launcher                                     DONE
                        DUEL_WINNER = 25, # "Duel winner", # duel winner                                                                DONE
                        SNIPER = 26, # "Sniper", # direct hit > 40                                                                      DONE
                        RAINBOW_FLAG = 27, # "Like rainbow flag - I hope today is not Aug 2",  # 10+ each of armors                     DONE
                        PERSONAL_STALKER = 28, # "Personal stalker", # killed one player more than all others taken together            DONE
                        SELF_DESTRUCTOR = 29, # "Self destructor - the main your enemy is yourself", # suicided more than killed any other player               DONE
                        OVERTIME_LOOSERS = 30, # "Looooooosers go home", # both the 1st and the 2nd places before overtime are finally below the 2nd place          #TODO
                        PHENIX_BIRD = 31, # "Like a Phoenix bird", # won after the last place in the middle of the game                 #TODO
                        TEAM_BEST_FRIEND_KILLER = 32, # "With friends like that, who needs enemies?" # maximum team kills               DONE
                        TEAM_MAXIMUM_TEAMDEATHS = 33, # "My friends are THE BEST OF THE BEST!!" # maximum team deaths                   DONE
                        LUMBERJACK = 34, # "Lumberjack" # 3+ axe kills                                                                  DONE
                        ELECTROMASTER = 35, # "Electomaster" # 40%+ and 20+ kills by shaft (thanks to Onanim)                           DONE
                        WHITEWASH = 36, # "Whitewash - full duel victory and total domination" # dry win duel                           DONE
                        FASTER_THAN_BULLET = 37,  # "Faster than bullet"  # streak 5+, 3.0- seconds per kill                            DONE
                        DEATH_CHEATER = 38,  # "Death cheater"  # less than 50% of average deaths                                       DONE
                        TEAMMATES_FAN = 39,  # "Teammates fan - no team deaths and no team kills"  # no teamkills and no teamdeaths     DONE
                        NO_SUICIDES = 40, # "I love this life!! No suicides at all"  # no suicides                                      DONE
                        UNIVERSAL_SOLDIER = 41, # "Killed players with more than 5 weapons"                                             DONE
                        MULTIPLE_PENETRATION = 42, # "Got killed with more than 5 weapons"                                              DONE
                        LONG_LIVE_KING = 43, #"Long Live and Prosper Like A King",  # the 1st 60 seconds without deaths                 DONE
                        HULK_SMASH = 44, #"Hulk SMASH!!" : "frags number {0:d} much more that the 2nd place({1:d})"  # the 1st place frags is twice bigger than the 2nd place  DONE
                        KILL_STREAK = 45, # "Killing without rest" # 15+ kill streak                                                    DONE
                        CHILD_LOVER = 46, # "Children are the flowers of our lives - no spawn frags"                                    DONE
                        GL_LOVER = 47,  # "Grenades is my passion!"  # 45%+ and 20+ kills by gl                                         DONE
                        BALANCED_PLAYER = 48, # "Balanced player - no one wants to lose: all %d duels are draws"                        DONE
                        LIKE_AN_ANGEL = 49,  # "Like an angel - NO damage to teammates at all!!"  #XML_SPECIFIC                         DONE
                        COMBO_DOUBLE_KILL = 50,  # "Two budgies slain with but a single missile" : "killed %s and %s with one %s shot!"   #two kills with on shot  #XML_SPECIFIC    DONE
                        COMBO_MUTUAL_KILL = 51,  # "Fight to the death!!" : "fought bravely until the last blood drop %d times"     3+ mutual kills   #XML_SPECIFIC                 DONE
                        COMBO_KAMIKAZE = 52,  # "Kamikaze - one way ticket!!" : "The sun on the wings - move forward! For the last time, the enemy will see the sunrise! One plane for one enemy! %d times..."  3+ suicide+kill   #XML_SPECIFIC    DONE
                        COMBO_TRIPLE_KILL = 53,  # "Three enemies with a single shot" : "killed %s, %s and %s with one %s shot!"   #three kills with on shot  #XML_SPECIFIC    DONE
                        KILLSTEAL_STEALER = 54,  # "King of theft" : "stole %d kills" # maximum kill steals - stealer                                           #DEATHMATCH_SPECIFIC   DONE
                        KILLSTEAL_VICTIM = 55,   # "Too unlucky and carefree..." : "honestly earned kills were stolen %d times" # maximum kill steals - victim  #DEATHMATCH_SPECIFIC   DONE
                        
                                            )

AchievementLevel = enum(UNKNOWN=0, BASIC_POSITIVE=1, BASIC_NEGATIVE=2, ADVANCE_POSITIVE=3, ADVANCE_NEGATIVE=5, RARE_POSITIVE=6, RARE_NEGATIVE=7, ULTRA_RARE=8)
                                            
class Achievement:
    def __init__(self, achtype, extra_info = ""):
        self.achtype = achtype
        self.extra_info = extra_info
        self.count = 1
        self.achlevel = self.level()

    def toString(self):
        for key in AchievementType.__dict__.keys():
            if AchievementType.__dict__.get(key) == self.achtype:
                return key

    def generateHtml(self, path = "ezquakestats/img/", size = 150):
        return "<img src=\"%s\" alt=\"%s\" title=\"%s: %s\" style=\"width:%dpx;height:%dpx;\">" % (self.getImgSrc(path), self.description(), self.description(), self.extra_info, size, size)
        
    def generateHtmlEx(self, path = "ezquakestats/img/", size = 125, radius = 45, shadowSize = 8, shadowIntensity = 35):
        return "<div style=\"position: relative;\">" \
               "<img src=\"%s\" alt=\"%s\" title=\"%s: %s\" style=\"width:%dpx;height:%dpx;border: 8px solid %s; -webkit-border-radius: %d%%; -moz-border-radius: %d%%; border-radius: %d%%;box-shadow: 0px 0px %dpx %dpx rgba(0,0,0,0.%d);\">" \
               "</div>" \
               % (self.getImgSrc(path), self.description(), self.description(), self.extra_info, size, size, Achievement.getBorderColor(self.achlevel), radius, radius, radius, shadowSize, shadowSize, shadowIntensity)
               
    @staticmethod
    def generateHtmlExCnt(ach, extraInfo, count, path = "ezquakestats/img/", size = 125, radius = 45, shadowSize = 8, shadowIntensity = 35):
        res = "<div style=\"position: relative;\">" \
               "<img src=\"%s\" alt=\"%s\" title=\"%s: \n%s\" style=\"width:%dpx;height:%dpx;border: 8px solid %s; -webkit-border-radius: %d%%; -moz-border-radius: %d%%; border-radius: %d%%;box-shadow: 0px 0px %dpx %dpx rgba(0,0,0,0.%d);\">" \
               % (ach.getImgSrc(path), ach.description(), ach.description(), extraInfo, size, size, Achievement.getBorderColor(ach.achlevel), radius, radius, radius, shadowSize, shadowSize, shadowIntensity)
    
        if count >= 0 and count < 10:
            res += "<img style=\"background-color:%s;position: absolute; top: 0; right: 0;width:37px;height:37px;border: 0px solid black;-webkit-border-radius: 55%%; -moz-border-radius: 55%%;" \
                   "border-radius:    55%%;box-shadow: 0px 0px 6px 6px rgba(0,0,0,0.25);\" src=\"%s\\nums\\num%d.png\" alt=\"\" >" \
                   % (Achievement.getBorderColor(ach.achlevel), path, count)
        elif count >= 10 and count < 100:
            res += "<div>" \
                   "<img style=\"background-color:%s;position: absolute; top: 0; right: 0;width:57px;height:37px;border: 0px solid black;-webkit-border-radius: 55%%;" \
                   "-moz-border-radius: 55%%; border-radius: 55%%;box-shadow: 0px 0px 6px 6px rgba(0,0,0,0.25);\" src=\"\" alt=\"\" >" \
                   "<img style=\"position: absolute; top: 3px; right: 24px;width:27px;height:33px;\" src=\"%s\\nums\\num%d.png\" alt=\"\" >" \
                   "<img style=\"position: absolute; top: 3px; right: 5px;width:27px;height:33px;\" src=\"%s\\nums\\num%d.png\" alt=\"\" >" \
                   "</div>" \
                   % (Achievement.getBorderColor(ach.achlevel), path, count / 10, path, count % 10)
        elif count >= 100 and count < 1000:
            res += "<div>" \
                   "<img style=\"background-color:%s;position: absolute; top: 0; right: 0;width:57px;height:37px;border: 0px solid black;-webkit-border-radius: 55%%;" \
                   "-moz-border-radius: 55%%; border-radius: 55%%;box-shadow: 0px 0px 6px 6px rgba(0,0,0,0.25);\" src=\"\" alt=\"\" >" \
                   "<img style=\"position: absolute; top: 6px; right: 35px;width:22px;height:28px;\" src=\"%s\\nums\\num%d.png\" alt=\"\" >" \
                   "<img style=\"position: absolute; top: 6px; right: 20px;width:22px;height:28px;\" src=\"%s\\nums\\num%d.png\" alt=\"\" >" \
                   "<img style=\"position: absolute; top: 6px; right: 3px;width:22px;height:28px;\" src=\"%s\\nums\\num%d.png\" alt=\"\" >" \
                   "</div>" \
                   % (Achievement.getBorderColor(ach.achlevel), path, count / 100, path, (count % 100) / 10, path, (count % 100) % 10)
        
        res += "</div>"
        return res
    
    def description(self):
        if self.achtype == AchievementType.LONG_LIVE:
            return "Long Live and Prosper"
        if self.achtype == AchievementType.SUICIDE_MASTER:
            return "Suicide Master"
        if self.achtype == AchievementType.SUICIDE_KING:
            return "Suicide King"
        if self.achtype == AchievementType.DEATH_STREAK_PAIN:
            return "What do you know about the pain?..."
        if self.achtype == AchievementType.GREAT_FINISH:
            return "Great Finish"
        if self.achtype == AchievementType.HORRIBLE_FINISH:
            return "Horrible Finish - finished to play too early"
        if self.achtype == AchievementType.ALWAYS_THE_FIRST:
            return "Always the 1st"
        if self.achtype == AchievementType.OVERTIME:
            return "One of who didn't want to give up"
        if self.achtype == AchievementType.SECOND_OVERTIME_REASON:
            return "The 2nd overtime!"
        if self.achtype == AchievementType.HUNDRED_KILLS:
            return "More than 100 kills"
        if self.achtype == AchievementType.HUNDRED_DEATHS:
            return "More than 100 deaths"
        if self.achtype == AchievementType.HUNDRED_FRAGS:
            return "More than 100 frags"
        if self.achtype == AchievementType.RED_ARMOR_EATER:
            return "Red armor eater"
        if self.achtype == AchievementType.GREEN_ARMOR_EATER:
            return "Green armor eater"
        if self.achtype == AchievementType.YELLOW_ARMOR_EATER:
            return "Yellow armor eater"
        if self.achtype == AchievementType.MEGA_HEALTH_EATER:
            return "Mega healths eater"
        if self.achtype == AchievementType.RED_ARMOR_ALLERGY:
            return "Red armor allergy - no red armors"
        if self.achtype == AchievementType.GREEN_ARMOR_ALLERGY:
            return "Green armor allergy - no green armors"
        if self.achtype == AchievementType.YELLOW_ARMOR_ALLERGY:
            return "Yellow armor allergy - no yellow armors"
        if self.achtype == AchievementType.MEGA_HEALTH_ALLERGY:
            return "Mega healths allergy - no mega healths"
        if self.achtype == AchievementType.CHILD_KILLER:
            return "Child killer"
        if self.achtype == AchievementType.ALWAYS_THE_LAST:
            return "Always the last"
        if self.achtype == AchievementType.ROCKETS_LOVER:
            return "Rockets lover"
        if self.achtype == AchievementType.DUEL_WINNER:
            return "Duel winner"
        if self.achtype == AchievementType.SNIPER:
            return "Sniper"
        if self.achtype == AchievementType.RAINBOW_FLAG:
            return "Like rainbow flag - I hope today is not Aug 2"
        if self.achtype == AchievementType.PERSONAL_STALKER:
            return "Personal stalker"
        if self.achtype == AchievementType.FINISH_GURU:
            return "Finish Guru"
        if self.achtype == AchievementType.SELF_DESTRUCTOR:
            return "Self destructor - the main your enemy is yourself"
        if self.achtype == AchievementType.TEAM_BEST_FRIEND_KILLER:
            return "With friends like that, who needs enemies?"
        if self.achtype == AchievementType.TEAM_MAXIMUM_TEAMDEATHS:
            return "My friends are THE BEST OF THE BEST!!"
        if self.achtype == AchievementType.LUMBERJACK:
            return "Lumberjack"
        if self.achtype == AchievementType.ELECTROMASTER:
            return "Electomaster - I like to roast"
        if self.achtype == AchievementType.WHITEWASH:
            return "Whitewash - full duel victory and total domination"
        if self.achtype == AchievementType.FASTER_THAN_BULLET:
            return "Faster than bullet"
        if self.achtype == AchievementType.DEATH_CHEATER:
            return "Death cheater"
        if self.achtype == AchievementType.TEAMMATES_FAN:
            return "Teammates fan - no team deaths and no team kills"
        if self.achtype == AchievementType.NO_SUICIDES:
            return "I love this life!! No suicides at all"
        if self.achtype == AchievementType.UNIVERSAL_SOLDIER:
            return 'Can handle any weapon'
        if self.achtype == AchievementType.MULTIPLE_PENETRATION:
            return 'So many different holes in your body:('
        if self.achtype == AchievementType.LONG_LIVE_KING:
            return "Long Live and Prosper Like A King"
        if self.achtype == AchievementType.HULK_SMASH:
            return "Hulk SMASH!!"
        if self.achtype == AchievementType.KILL_STREAK:
            return "Killing without rest"
        if self.achtype == AchievementType.CHILD_LOVER:
            return "Children are the flowers of our lives - no spawn frags"
        if self.achtype == AchievementType.GL_LOVER:
            return "Grenades is my passion!"
        if self.achtype == AchievementType.BALANCED_PLAYER:
            return "Balanced player - no one wants to lose"
        if self.achtype == AchievementType.LIKE_AN_ANGEL:
            return "Like an angel - NO damage to teammates at all!!"
        if self.achtype == AchievementType.COMBO_DOUBLE_KILL:
            return "Two budgies slain with but a single missile"
        if self.achtype == AchievementType.COMBO_MUTUAL_KILL:
            return "Fight to the death!!"
        if self.achtype == AchievementType.COMBO_KAMIKAZE:
            return "Kamikaze - one way ticket!!"
        if self.achtype == AchievementType.COMBO_TRIPLE_KILL:
            return "Three enemies with a single shot"
        if self.achtype == AchievementType.KILLSTEAL_STEALER:
            return "King of theft"
        if self.achtype == AchievementType.KILLSTEAL_VICTIM:
            return "Too unlucky and carefree..."

    # AchievementLevel = enum(UNKNOWN=0, BASIC_POSITIVE=1, BASIC_NEGATIVE=2, ADVANCE_POSITIVE=3, ADVANCE_NEGATIVE=5, RARE_POSITIVE=6, RARE_NEGATIVE=7, ULTRA_RARE=8)
    def level(self):
        if self.achtype == AchievementType.RED_ARMOR_EATER    or \
           self.achtype == AchievementType.GREEN_ARMOR_EATER  or \
           self.achtype == AchievementType.YELLOW_ARMOR_EATER or \
           self.achtype == AchievementType.MEGA_HEALTH_EATER  or \
           self.achtype == AchievementType.CHILD_KILLER       or \
           self.achtype == AchievementType.ROCKETS_LOVER:
            return AchievementLevel.BASIC_POSITIVE
            
        if self.achtype == AchievementType.SUICIDE_MASTER          or \
           self.achtype == AchievementType.DEATH_STREAK_PAIN       or \
           self.achtype == AchievementType.RED_ARMOR_ALLERGY       or \
           self.achtype == AchievementType.GREEN_ARMOR_ALLERGY     or \
           self.achtype == AchievementType.YELLOW_ARMOR_ALLERGY    or \
           self.achtype == AchievementType.MEGA_HEALTH_ALLERGY     or \
           self.achtype == AchievementType.TEAM_BEST_FRIEND_KILLER or \
           self.achtype == AchievementType.TEAM_MAXIMUM_TEAMDEATHS:
            return AchievementLevel.BASIC_NEGATIVE            
            
        if self.achtype == AchievementType.LONG_LIVE          or \
           self.achtype == AchievementType.ALWAYS_THE_FIRST   or \
           self.achtype == AchievementType.OVERTIME           or \
           self.achtype == AchievementType.DUEL_WINNER        or \
           self.achtype == AchievementType.PERSONAL_STALKER   or \
           self.achtype == AchievementType.FASTER_THAN_BULLET or \
           self.achtype == AchievementType.TEAMMATES_FAN      or \
           self.achtype == AchievementType.NO_SUICIDES        or \
           self.achtype == AchievementType.CHILD_LOVER        or \
           self.achtype == AchievementType.GL_LOVER           or \
           self.achtype == AchievementType.COMBO_KAMIKAZE     or \
           self.achtype == AchievementType.KILLSTEAL_STEALER:
            return AchievementLevel.ADVANCE_POSITIVE            
            
        if self.achtype == AchievementType.SUICIDE_KING    or \
           self.achtype == AchievementType.ALWAYS_THE_LAST or \
           self.achtype == AchievementType.SELF_DESTRUCTOR or \
           self.achtype == AchievementType.KILLSTEAL_VICTIM:
            return AchievementLevel.ADVANCE_NEGATIVE            
               
        if self.achtype == AchievementType.GREAT_FINISH           or \
           self.achtype == AchievementType.SECOND_OVERTIME_REASON or \
           self.achtype == AchievementType.HUNDRED_KILLS          or \
           self.achtype == AchievementType.FINISH_GURU            or \
           self.achtype == AchievementType.ELECTROMASTER          or \
           self.achtype == AchievementType.SNIPER                 or \
           self.achtype == AchievementType.DEATH_CHEATER          or \
           self.achtype == AchievementType.UNIVERSAL_SOLDIER      or \
           self.achtype == AchievementType.LONG_LIVE_KING         or \
           self.achtype == AchievementType.HULK_SMASH             or \
           self.achtype == AchievementType.KILL_STREAK            or \
           self.achtype == AchievementType.BALANCED_PLAYER        or \
           self.achtype == AchievementType.LIKE_AN_ANGEL          or \
           self.achtype == AchievementType.WHITEWASH              or \
           self.achtype == AchievementType.COMBO_DOUBLE_KILL      or \
           self.achtype == AchievementType.COMBO_MUTUAL_KILL:
            return AchievementLevel.RARE_POSITIVE
      
        if self.achtype == AchievementType.HORRIBLE_FINISH  or \
           self.achtype == AchievementType.HUNDRED_DEATHS   or \
           self.achtype == AchievementType.MULTIPLE_PENETRATION:
            return AchievementLevel.RARE_NEGATIVE            
            
        if self.achtype == AchievementType.HUNDRED_FRAGS or \
           self.achtype == AchievementType.RAINBOW_FLAG  or \
           self.achtype == AchievementType.LUMBERJACK    or \
           self.achtype == AchievementType.COMBO_TRIPLE_KILL:
            return AchievementLevel.ULTRA_RARE            

    @staticmethod    
    def getBorderColor(achlevel):
        # if achlevel == AchievementLevel.BASIC_POSITIVE:
            # return "green"
        # if achlevel == AchievementLevel.BASIC_NEGATIVE:
            # return "#b32f25"  # dark red
        # if achlevel == AchievementLevel.ADVANCE_POSITIVE:
            # return "#09e9ed"  
        # if achlevel == AchievementLevel.ADVANCE_NEGATIVE:
            # return "#f02313"  # light red
        # if achlevel == AchievementLevel.RARE_POSITIVE:
            # return "gold"
        # if achlevel == AchievementLevel.RARE_NEGATIVE:
            # return "#391366"  # dark purple
        # if achlevel == AchievementLevel.ULTRA_RARE:
            # return "#cd0ceb"  # purple
            
        if achlevel == AchievementLevel.BASIC_POSITIVE or \
           achlevel == AchievementLevel.BASIC_NEGATIVE:
            return "green"
            
        if achlevel == AchievementLevel.ADVANCE_POSITIVE or \
           achlevel == AchievementLevel.ADVANCE_NEGATIVE:
            return "#09e9ed"  
        
        if achlevel == AchievementLevel.RARE_POSITIVE or \
           achlevel == AchievementLevel.RARE_NEGATIVE:
            return "gold"

        if achlevel == AchievementLevel.ULTRA_RARE:
            return "#cd0ceb"  # purple            

    @staticmethod
    def generateAchievementsLevelLegendTable(oneLine = True):
        achLevelsHtmlTable = HTML.Table(border="0", cellspacing="0", style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 8pt;")

        if oneLine:
            achLevelsHtmlTable.rows.append( HTML.TableRow(cells=[ 
                                HTML.TableCell("<pre> </pre>", bgcolor=Achievement.getBorderColor(AchievementLevel.BASIC_NEGATIVE)),
                                HTML.TableCell("Basic level"),
                                HTML.TableCell("<pre>   </pre>"),
    
                                HTML.TableCell("<pre> </pre>", bgcolor=Achievement.getBorderColor(AchievementLevel.ADVANCE_NEGATIVE)),
                                HTML.TableCell("Advanced level"),
                                HTML.TableCell("<pre>   </pre>"),
    
                                HTML.TableCell("<pre> </pre>", bgcolor=Achievement.getBorderColor(AchievementLevel.RARE_NEGATIVE)),                                
                                HTML.TableCell("Rare level"),
                                HTML.TableCell("<pre>   </pre>"),
    
                                HTML.TableCell("<pre> </pre>", bgcolor=Achievement.getBorderColor(AchievementLevel.ULTRA_RARE)),                                    
                                HTML.TableCell("UltraRare level") ] ))

        else:
            achLevelsHtmlTable.rows.append( HTML.TableRow(cells=[ 
                                        HTML.TableCell("<pre> </pre>", bgcolor=Achievement.getBorderColor(AchievementLevel.BASIC_NEGATIVE)),
                                        HTML.TableCell(" "),
                                        HTML.TableCell("<pre> </pre>", bgcolor=Achievement.getBorderColor(AchievementLevel.BASIC_POSITIVE)),
                                        HTML.TableCell("Basic level"),
                                        HTML.TableCell("<pre>   </pre>"),
            
                                        HTML.TableCell("<pre> </pre>", bgcolor=Achievement.getBorderColor(AchievementLevel.ADVANCE_NEGATIVE)),
                                        HTML.TableCell(" "),
                                        HTML.TableCell("<pre> </pre>", bgcolor=Achievement.getBorderColor(AchievementLevel.ADVANCE_POSITIVE)),
                                        HTML.TableCell("Advanced level"),
                                        HTML.TableCell("<pre>   </pre>"),
            
                                        HTML.TableCell("<pre> </pre>", bgcolor=Achievement.getBorderColor(AchievementLevel.RARE_NEGATIVE)),
                                        HTML.TableCell(" "),
                                        HTML.TableCell("<pre> </pre>", bgcolor=Achievement.getBorderColor(AchievementLevel.RARE_POSITIVE)),
                                        HTML.TableCell("Rare level"),
                                        HTML.TableCell("<pre>   </pre>"),
            
                                        HTML.TableCell("<pre> </pre>", bgcolor=Achievement.getBorderColor(AchievementLevel.ULTRA_RARE)),                                    
                                        HTML.TableCell("UltraRare level") ] ))
                                    
        return str(achLevelsHtmlTable)
                    
    def getImgSrc(self, path):
        if self.achtype == AchievementType.LONG_LIVE:
            return path + "ach_long_liver.jpg"
        if self.achtype == AchievementType.SUICIDE_MASTER:
            return path + "ach_suicide_master.jpg"
        if self.achtype == AchievementType.SUICIDE_KING:
            return path + "ach_suicide_king.jpg"
        if self.achtype == AchievementType.DEATH_STREAK_PAIN:
            return path + "ach_death_pain.jpg"
        if self.achtype == AchievementType.HORRIBLE_FINISH:
            return path + "ach_horrible_finish.jpg"
        if self.achtype == AchievementType.RED_ARMOR_EATER:
            return path + "ach_ra_eater.jpg"
        if self.achtype == AchievementType.GREEN_ARMOR_EATER:
            return path + "ach_ga_eater.jpg"
        if self.achtype == AchievementType.YELLOW_ARMOR_EATER:
            return path + "ach_ya_eater.jpg"
        if self.achtype == AchievementType.MEGA_HEALTH_EATER:
            return path + "ach_mh_eater.jpg"
        if self.achtype == AchievementType.CHILD_KILLER:
            return path + "ach_child_killer.png"
        if self.achtype == AchievementType.ALWAYS_THE_LAST:
            return path + "ach_always_the_last.jpg"
        if self.achtype == AchievementType.RED_ARMOR_ALLERGY:
            return path + "ach_ra_allergy.jpg"
        if self.achtype == AchievementType.GREEN_ARMOR_ALLERGY:
            return path + "ach_ga_allergy.jpg"
        if self.achtype == AchievementType.YELLOW_ARMOR_ALLERGY:
            return path + "ach_ya_allergy.jpg"
        if self.achtype == AchievementType.MEGA_HEALTH_ALLERGY:
            return path + "ach_mh_allergy.jpg"
        if self.achtype == AchievementType.ROCKETS_LOVER:
            return path + "ach_rockets_lover.png"
        if self.achtype == AchievementType.DUEL_WINNER:
            return path + "ach_duel_winner.jpg"
        if self.achtype == AchievementType.SNIPER:
            return path + "ach_sniper.jpg"
        if self.achtype == AchievementType.RAINBOW_FLAG:
            return path + "ach_rainbow_flag.jpg"
        if self.achtype == AchievementType.PERSONAL_STALKER:
            return path + "ach_personal_stalker.jpg"
        if self.achtype == AchievementType.FINISH_GURU:
            return path + "ach_finish_guru.jpg"
        if self.achtype == AchievementType.SELF_DESTRUCTOR:
            return path + "ach_self_destructor.jpg"
        if self.achtype == AchievementType.TEAM_BEST_FRIEND_KILLER:
            return path + "ach_team_killer.jpg"
        if self.achtype == AchievementType.TEAM_MAXIMUM_TEAMDEATHS:
            return path + "ach_team_deaths.jpg"
        if self.achtype == AchievementType.LUMBERJACK:
            return path + "ach_lumberjack.jpg"
        if self.achtype == AchievementType.ELECTROMASTER:
            return path + "ach_electromaster.png"
        if self.achtype == AchievementType.WHITEWASH:
            return path + "ach_whitewash.png"
        if self.achtype == AchievementType.FASTER_THAN_BULLET:
            return path + "ach_faster_than_bullet.png"
        if self.achtype == AchievementType.DEATH_CHEATER:
            return path + "ach_death_cheater.jpg"
        if self.achtype == AchievementType.TEAMMATES_FAN:
            return path + "ach_teammates_fan.jpg"
        if self.achtype == AchievementType.NO_SUICIDES:
            return path + "ach_no_suicides.jpg"
        if self.achtype == AchievementType.UNIVERSAL_SOLDIER:
            return path + "ach_universal_soldier.jpg"
        if self.achtype == AchievementType.MULTIPLE_PENETRATION:
            return path + "ach_multiple_penetration.jpg"
        if self.achtype == AchievementType.LONG_LIVE_KING:
            return path + "ach_long_liver_king.jpg"
        if self.achtype == AchievementType.HULK_SMASH:
            return path + "ach_hulk_smash.jpg"
        if self.achtype == AchievementType.KILL_STREAK:
            return path + "ach_kill_streak.jpg"
        if self.achtype == AchievementType.CHILD_LOVER:
            return path + "ach_child_lover.png"
        if self.achtype == AchievementType.GL_LOVER:
            return path + "ach_gl_lover.jpg"
        if self.achtype == AchievementType.BALANCED_PLAYER:
            return path + "ach_balanced_player.png"
        if self.achtype == AchievementType.LIKE_AN_ANGEL:
            return path + "ach_like_an_angel.png"
        if self.achtype == AchievementType.OVERTIME:
            return path + "ach_overtime.jpg"
        if self.achtype == AchievementType.COMBO_DOUBLE_KILL:
            return path + "ach_double_kill.png"
        if self.achtype == AchievementType.COMBO_MUTUAL_KILL:
            return path + "ach_combo_mutual_kill.png"
        if self.achtype == AchievementType.COMBO_KAMIKAZE:
            return path + "ach_combo_kamikaze.png"
        if self.achtype == AchievementType.ALWAYS_THE_FIRST:
            return path + "ach_always_the_first.jpg"
        if self.achtype == AchievementType.COMBO_TRIPLE_KILL:
            return path + "ach_combo_triple_kill.png"
        if self.achtype == AchievementType.KILLSTEAL_STEALER:
            return path + "ach_killsteal_stealer.png"
        if self.achtype == AchievementType.KILLSTEAL_VICTIM:
            return path + "ach_killsteal_victim.png"

        # temp images
        if self.achtype == AchievementType.HUNDRED_KILLS:
            return path + "ach_100_kills_TMP.jpg"
        if self.achtype == AchievementType.HUNDRED_DEATHS:
            return path + "ach_100_deaths_TMP.jpg"
        if self.achtype == AchievementType.HUNDRED_FRAGS:
            return path + "ach_100_frags_TMP.jpg"

        return "NotImplemented"

def calculateCommonAchievements(allplayers, headToHead, minutesPlayed, isTeamGame, headToHeadDamage = None):
    if isTeamGame:
        # TEAM_BEST_FRIEND_KILLER
        sortedByTeamkills = sorted(allplayers, key=attrgetter("teamkills"), reverse=True)
        maxTeamkillsVal = sortedByTeamkills[0].teamkills
        if maxTeamkillsVal >= 3:
            for pl in sortedByTeamkills:
                if pl.teamkills == maxTeamkillsVal:
                    pl.achievements.append( Achievement(AchievementType.TEAM_BEST_FRIEND_KILLER, "killed teammates %d times" % (pl.teamkills)) )

        # TEAM_MAXIMUM_TEAMDEATHS
        sortedByTeamdeaths = sorted(allplayers, key=attrgetter("teamdeaths"), reverse=True)
        maxTeamdeathsVal = sortedByTeamdeaths[0].teamdeaths
        if maxTeamdeathsVal >= 3:
            for pl in sortedByTeamdeaths:
                if pl.teamdeaths == maxTeamdeathsVal:
                    pl.achievements.append( Achievement(AchievementType.TEAM_MAXIMUM_TEAMDEATHS, "was killed by teammates %d times" % (pl.teamdeaths)) )

    # WHITEWASH
    if minutesPlayed != 0:
        for pl in allplayers:
            if pl.playTimeXML() > ((minutesPlayed / 2) * 60):
                for plname,elem in headToHead.items():
                    for plElem in elem:
                        if plElem[0] == pl.name and plElem[1] == 0:
                            pnts = 0
                            for elem2 in headToHead[pl.name]:
                                if elem2[0] == plname:
                                    pnts = elem2[1]
                            if pnts != 0:
                                # check for teammates
                                isEnemy = False
                                enemyPlayTime = 0
                                for pl2 in allplayers:
                                    if pl2.name == plname:
                                        isEnemy = pl2.teamname != pl.teamname
                                        enemyPlayTime = pl2.playTimeXML()
                                        break
                                if isEnemy or (pl.teamname == ""):
                                    if enemyPlayTime >= ((minutesPlayed / 2) * 60):
                                        pl.achievements.append( Achievement(AchievementType.WHITEWASH, "duel with %s is fully won, score is %d:0" % (plname, pnts)) )

    # DEATH_CHEATER
    deathsSum = 0
    for pl in allplayers:
        if pl.playTimeXML() >= ((minutesPlayed*3 / 4) * 60):
            deathsSum += pl.deaths

    avgDeathsCount = deathsSum / len(allplayers)

    for pl in allplayers:
        if pl.playTimeXML() >= ((minutesPlayed*3 / 4) * 60):
            if pl.deaths < (int)(avgDeathsCount * 0.5):
                pl.achievements.append( Achievement(AchievementType.DEATH_CHEATER, "died only {0:d} times ({1:5.3}% of the average)".format(pl.deaths, (float(pl.deaths) / float(avgDeathsCount) * 100))) )

    # HULK_SMASH
    if len(allplayers) >= 2:
        sortedByFrags = sorted(allplayers, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)
        if sortedByFrags[0].frags() >= sortedByFrags[1].frags()*1.75:
            sortedByFrags[0].achievements.append( Achievement(AchievementType.HULK_SMASH, "frags number {0:d} much more that the 2nd place({1:d})".format(sortedByFrags[0].frags(), sortedByFrags[1].frags())) )

    # BALANCED_PLAYER
    if len(allplayers) >= 3:
        for pl in allplayers:
            if pl.playTimeXML() >= ((minutesPlayed / 4) * 60):
                isAllDraws = True
                isAllNonZeros = True
                duelsNum = 0
                for pl2 in allplayers:
                    plKills = 0
                    plTeam = ""
                    for val in headToHead[pl.name]:
                        if val[0] == pl2.name:
                            plKills = val[1]
                            plTeam = pl2.teamname
                    
                    plDeaths = 0
                    for val in headToHead[pl2.name]:
                        if val[0] == pl.name:
                            plDeaths = val[1]               
                    
                    if isTeamGame and pl.teamname == plTeam:
                        continue
                    
                    duelsNum += 1
                    
                    if plKills == 0 and plDeaths == 0:
                        isAllNonZeros = False
                    
                    if plKills != plDeaths:
                        isAllDraws = False
                        break

                if isAllNonZeros and isAllDraws:
                    pl.achievements.append( Achievement(AchievementType.BALANCED_PLAYER, "all %d duels are draws" % (duelsNum)) )

    # LIKE_AN_ANGEL
    if isTeamGame and not headToHeadDamage is None and headToHeadDamage != {}:
        if len(allplayers) >= 3:
            for pl in allplayers:
                if pl.playTimeXML() >= ((minutesPlayed / 2) * 60):
                    isNoTeamDamage = True
                    for pl2 in allplayers:
                        plKillDamage = 0
                        plTeam = ""
                        for val in headToHeadDamage[pl.name]:
                            if val[0] == pl2.name:
                                plKillDamage = val[1]
                                plTeam = pl2.teamname
                        
                        plDeathDamage = 0
                        for val in headToHeadDamage[pl2.name]:
                            if val[0] == pl.name:
                                plDeathDamage = val[1]
                        
                        if pl.teamname == plTeam and pl.name != pl2.name:
                            if plKillDamage != 0:
                                isNoTeamDamage = False
                                break
                                
                    if isNoTeamDamage:
                        pl.achievements.append( Achievement(AchievementType.LIKE_AN_ANGEL) )
                        
    # KILLSTEAL_STEALER
    # KILLSTEAL_STEALER
    if not isTeamGame:
        maxStealsStealer = -1
        maxStealsVictim  = -1
        for pl in allplayers:
            if len(pl.killsteals_stealer) >= maxStealsStealer:
                maxStealsStealer = len(pl.killsteals_stealer)
            if len(pl.killsteals_victim) >= maxStealsVictim:
                maxStealsVictim = len(pl.killsteals_victim)
        
        for pl in allplayers:
            if maxStealsStealer >= 3 and len(pl.killsteals_stealer) == maxStealsStealer:
                pl.achievements.append( Achievement(AchievementType.KILLSTEAL_STEALER, "stole %d kills" % (len(pl.killsteals_stealer))) )
            if maxStealsVictim >= 3 and len(pl.killsteals_victim) == maxStealsVictim:
                pl.achievements.append( Achievement(AchievementType.KILLSTEAL_VICTIM, "honestly earned kills were stolen %d times" % (len(pl.killsteals_victim))) )
                
class Team:
    def __init__(self, teamname):
        self.name = teamname
        self.ga = 0
        self.ya = 0
        self.ra = 0
        self.mh = 0
        self.tkn = 0
        self.gvn = 0
        self.tm  = 0

        self.kills = 0
        self.deaths = 0
        self.suicides = 0
        self.teamkills = 0
        self.teamdeaths = 0

        self.gaByMinutes = []
        self.yaByMinutes = []
        self.raByMinutes = []
        self.mhByMinutes = []

        self.powerUps = []

        self.rl_kills = 0
        self.lg_kills = 0
        self.gl_kills = 0
        self.sg_kills = 0
        self.ssg_kills = 0
        self.ng_kills = 0
        self.sng_kills = 0
        self.axe_kills = 0
        self.tele_kills = 0
        self.other_kills = 0
        #self.TODO_kills = 0

        self.rl_deaths = 0
        self.lg_deaths = 0
        self.gl_deaths = 0
        self.sg_deaths = 0
        self.ssg_deaths = 0
        self.ng_deaths = 0
        self.sng_deaths = 0
        self.axe_deaths = 0
        self.tele_deaths = 0
        self.other_deaths = 0
        #self.TODO_deaths = 0

        # XML data
        self.damageSelf = 0
        self.damageGvn = 0
        self.damageTkn = 0
        self.damageSelfArmor = 0
        self.damageGvnArmor = 0
        self.damageTknArmor = 0        
        
    def damageDelta(self):
        return (self.gvn - self.tkn)

    def frags(self):
        return (self.kills - self.teamkills - self.suicides);

    def initPowerUpsByMinutes(self, minutesCnt):
        self.gaByMinutes = [0 for i in xrange(minutesCnt+1)]
        self.yaByMinutes = [0 for i in xrange(minutesCnt+1)]
        self.raByMinutes = [0 for i in xrange(minutesCnt+1)]
        self.mhByMinutes = [0 for i in xrange(minutesCnt+1)]

    def fillWeaponsKillsDeaths(self, player):
        self.rl_kills += player.rl_kills
        self.lg_kills += player.lg_kills
        self.gl_kills += player.gl_kills
        self.sg_kills += player.sg_kills
        self.ssg_kills += player.ssg_kills
        self.ng_kills += player.ng_kills
        self.sng_kills += player.sng_kills
        self.axe_kills += player.axe_kills
        self.tele_kills += player.tele_kills
        self.other_kills += player.other_kills
        #self.TODO_kills += player.TODO_kills

        self.rl_deaths += player.rl_deaths
        self.lg_deaths += player.lg_deaths
        self.gl_deaths += player.gl_deaths
        self.sg_deaths += player.sg_deaths
        self.ssg_deaths += player.ssg_deaths
        self.ng_deaths += player.ng_deaths
        self.sng_deaths += player.sng_deaths
        self.axe_deaths += player.axe_deaths
        self.tele_deaths += player.tele_deaths
        self.other_deaths += player.other_deaths
        #self.TODO_deaths += player.TODO_deaths

    def getWeaponsKills(self, totalValue, weaponsCheck):
        rlstr   = "" if not weaponsCheck.is_rl    or totalValue == 0 else "rl:{0:3d}({1:5.4}%), ".format(  self.rl_kills,   (float(self.rl_kills)   / float(totalValue) * 100));
        lgstr   = "" if not weaponsCheck.is_lg    or totalValue == 0 else "lg:{0:3d}({1:6.3}%), ".format(  self.lg_kills,   (float(self.lg_kills)   / float(totalValue) * 100));
        glstr   = "" if not weaponsCheck.is_gl    or totalValue == 0 else "gl:{0:3d}({1:6.3}%), ".format(  self.gl_kills,   (float(self.gl_kills)   / float(totalValue) * 100));
        sgstr   = "" if not weaponsCheck.is_sg    or totalValue == 0 else "sg:{0:3d}({1:6.3}%), ".format(  self.sg_kills,   (float(self.sg_kills)   / float(totalValue) * 100));
        ssgstr  = "" if not weaponsCheck.is_ssg   or totalValue == 0 else "ssg:{0:3d}({1:6.3}%), ".format( self.ssg_kills,  (float(self.ssg_kills)  / float(totalValue) * 100));
        ngstr   = "" if not weaponsCheck.is_ng    or totalValue == 0 else "ng:{0:3d}({1:6.3}%), ".format(  self.ng_kills,   (float(self.ng_kills)   / float(totalValue) * 100));
        sngstr  = "" if not weaponsCheck.is_sng   or totalValue == 0 else "sng:{0:3d}({1:6.3}%), ".format( self.sng_kills,  (float(self.sng_kills)  / float(totalValue) * 100));
        axestr  = "" if not weaponsCheck.is_axe   or totalValue == 0 else "axe:{0:3d}({1:6.3}%), ".format( self.axe_kills,  (float(self.axe_kills)  / float(totalValue) * 100));
        telestr = "" if not weaponsCheck.is_tele  or totalValue == 0 else "tele:{0:3d}({1:6.3}%), ".format(self.tele_kills, (float(self.tele_kills) / float(totalValue) * 100));
        otherstr= "" if not weaponsCheck.is_other or totalValue == 0 else "other:{0:3d}({1:6.3}%), ".format( self.other_kills,  (float(self.other_kills)  / float(totalValue) * 100));

        resstr = "%s%s%s%s%s%s%s%s%s%s" % (rlstr, lgstr, glstr, sgstr, ssgstr, ngstr, sngstr, axestr, telestr, otherstr);
        if len(resstr) > 2:
            resstr = resstr[:-2]
        return resstr

    def getWeaponsDeaths(self, totalValue, weaponsCheck):
        rlstr   = "" if not weaponsCheck.is_rl    or totalValue == 0 else "rl:{0:3d}({1:5.4}%), ".format(  self.rl_deaths,   (float(self.rl_deaths)   / float(totalValue) * 100));
        lgstr   = "" if not weaponsCheck.is_lg    or totalValue == 0 else "lg:{0:3d}({1:6.3}%), ".format(  self.lg_deaths,   (float(self.lg_deaths)   / float(totalValue) * 100));
        glstr   = "" if not weaponsCheck.is_gl    or totalValue == 0 else "gl:{0:3d}({1:6.3}%), ".format(  self.gl_deaths,   (float(self.gl_deaths)   / float(totalValue) * 100));
        sgstr   = "" if not weaponsCheck.is_sg    or totalValue == 0 else "sg:{0:3d}({1:6.3}%), ".format(  self.sg_deaths,   (float(self.sg_deaths)   / float(totalValue) * 100));
        ssgstr  = "" if not weaponsCheck.is_ssg   or totalValue == 0 else "ssg:{0:3d}({1:6.3}%), ".format( self.ssg_deaths,  (float(self.ssg_deaths)  / float(totalValue) * 100));
        ngstr   = "" if not weaponsCheck.is_ng    or totalValue == 0 else "ng:{0:3d}({1:6.3}%), ".format(  self.ng_deaths,   (float(self.ng_deaths)   / float(totalValue) * 100));
        sngstr  = "" if not weaponsCheck.is_sng   or totalValue == 0 else "sng:{0:3d}({1:6.3}%), ".format( self.sng_deaths,  (float(self.sng_deaths)  / float(totalValue) * 100));
        axestr  = "" if not weaponsCheck.is_axe   or totalValue == 0 else "axe:{0:3d}({1:6.3}%), ".format( self.axe_deaths,  (float(self.axe_deaths)  / float(totalValue) * 100));
        telestr = "" if not weaponsCheck.is_tele  or totalValue == 0 else "tele:{0:3d}({1:6.3}%), ".format(self.tele_deaths, (float(self.tele_deaths) / float(totalValue) * 100));
        otherstr= "" if not weaponsCheck.is_other or totalValue == 0 else "other:{0:3d}({1:6.3}%), ".format( self.other_deaths,  (float(self.other_deaths)  / float(totalValue) * 100));

        resstr = "%s%s%s%s%s%s%s%s%s%s" % (rlstr, lgstr, glstr, sgstr, ssgstr, ngstr, sngstr, axestr, telestr, otherstr);
        if len(resstr) > 2:
            resstr = resstr[:-2]
        return resstr


class WeaponsCheckRes:
    def __init__(self, val = False):
        for weap in possibleWeapons:
            exec("self.is_%s = %s" % (weap, "True" if val else "False"))

def getWeaponsCheck(allplayers):
    res = WeaponsCheckRes();
    for pl in allplayers:
        for weap in possibleWeapons:
           weapCheck = False
           exec("weapCheck = (pl.%s_kills != 0) or (pl.%s_deaths != 0);" % (weap, weap))
           if weapCheck:
               exec("res.is_%s = True;" % (weap));
    return res;

# XML STRUCTURES >>>>>
    
#<damage>
#<time>15.064777</time>
#<attacker>dinoel</attacker>
#<target>mche</target>
#<type>rl</type>
#<quad>0</quad>
#<splash>1</splash>
#<value>41</value>
#<armor>1</armor>
#</damage>

class DamageElement:
    def __init__(self):
        self.time = -1
        self.attacker = ""
        self.target = ""
        self.type = ""
        self.quad = -1
        self.splash = -1
        self.value = -1
        self.armor = -1

        self.isSelfDamage = False

    def __init__(self, elem):
        self.time = float(elem.find("time").text)
        self.attacker = elem.find("attacker").text
        self.target = elem.find("target").text
        self.type = elem.find("type").text
        self.quad = int(elem.find("quad").text)
        self.splash = int(elem.find("splash").text)
        self.value = int(elem.find("value").text)
        self.armor = int(elem.find("armor").text)

        self.isSelfDamage = self.attacker == self.target

    def toString(self):
        return "DamageElement: time=%f, attacker=%s, target=%s, type=%s, value=%f, armor=%d, isSelfDamage=%d\n" % (self.time,self.attacker,self.target,self.type,self.value,self.armor,self.isSelfDamage)

#<death>
#<time>18.817241</time>
#<attacker>dinoel</attacker>
#<target>Sasha</target>
#<type>rl</type>
#<quad>0</quad>
#<armorleft>84</armorleft>
#<killheight>0</killheight>
#<lifetime>18.570112</lifetime>
#</death>

class DeathElement:
    def __init__(self):
        self.time = -1
        self.attacker = ""
        self.target = ""
        self.type = ""
        self.quad = -1
        self.armorleft = -1
        self.killheight = -1
        self.lifetime = 0.0

        self.isSuicide = False
        self.isSpawnFrag = False

    def __init__(self, elem):
        self.time = float(elem.find("time").text)
        self.attacker = elem.find("attacker").text
        self.target = elem.find("target").text
        self.type = elem.find("type").text
        self.quad = int(elem.find("quad").text)
        self.armorleft = int(elem.find("armorleft").text)
        self.killheight = int(elem.find("killheight").text)
        self.lifetime = float(elem.find("lifetime").text)
        
        self.isSuicide = self.attacker == self.target
        self.isSpawnFrag = self.lifetime < 2.0
        
    def toString(self):
        return "DeathElement: time=%f, attacker=%s, target=%s, type=%s, armorleft=%d, lifetime=%f, isSuicide=%d, isSpawnFrag=%d\n" % (self.time,self.attacker,self.target,self.type,self.armorleft,self.lifetime,self.isSuicide,self.isSpawnFrag)

#<pick_mapitem>
#        <time>15.715332</time>
#        <item>item_armor1</item>
#        <player>Sasha</player>
#        <value>100</value>
#</pick_mapitem>

# items:
#    <item>health_100</item>
#    <item>health_15</item>
#    <item>health_25</item>
#    <item>item_armor1</item>     <-- GA
#    <item>item_armor2</item>     <-- YA
#    <item>item_armorInv</item>   <-- RA

#    <item>item_cells</item>
#    <item>item_rockets</item>
#    <item>item_spikes</item>

#    <item>weapon_grenadelauncher</item>
#    <item>weapon_lightning</item>
#    <item>weapon_rocketlauncher</item>
#    <item>weapon_supernailgun</item>
#    <item>weapon_supershotgun</item>                                


class PickMapItemElement:
    def __init__(self):
        self.time = -1
        self.item = ""
        self.player = ""
        self.value = -1

        self.isArmor = False
        self.isMH = False
        self.isHealth = False
        self.armorType = PowerUpType.UNKNOWN
              
    def __init__(self, elem):
        self.time = float(elem.find("time").text)
        self.item =  elem.find("item").text
        self.player =  elem.find("player").text
        self.value = int(elem.find("value").text) 

        self.isArmor = "item_armor" in self.item
        
        self.isMH = False
        self.isHealth = False        
        
        if "health" in self.item:
            if self.item == "health_100":
                self.isMH = True
            self.isHealth = True
        
        if self.isArmor:
            if self.item == "item_armor1":
                self.armorType = PowerUpType.GA
            if self.item == "item_armor2":
                self.armorType = PowerUpType.YA
            if self.item == "item_armorInv":
                self.armorType = PowerUpType.RA


# <<<<< XML STRUCTURES 




#    {WEAPON, 10, 1, "(.*) sleeps with the fishes", false},
#    {WEAPON, 10, 1, "(.*) sucks it down", false},
#    {WEAPON, 10, 1, "(.*) gulped a load of slime", false},
#    {WEAPON, 10, 1, "(.*) can't exist on slime alone", false},
#    {WEAPON, 10, 1, "(.*) burst into flames", false},
#    {WEAPON, 10, 1, "(.*) turned into hot slag", false},
#    {WEAPON, 10, 1, "(.*) visits the Volcano God", false},
#    {WEAPON, 15, 1, "(.*) cratered", false},
#    {WEAPON, 15, 1, "(.*) fell to his death", false},
#    {WEAPON, 15, 1, "(.*) fell to her death", false},
#    {WEAPON, 11, 1, "(.*) blew up", false},
#    {WEAPON, 11, 1, "(.*) was spiked", false},
#    {WEAPON, 11, 1, "(.*) was zapped", false},
#    {WEAPON, 11, 1, "(.*) ate a lavaball", false},
#    {WEAPON, 12, 1, "(.*) was telefragged by his teammate", false},
#    {WEAPON, 12, 1, "(.*) was telefragged by her teammate", false},
#    {WEAPON,  0, 1, "(.*) died", false},
#    {WEAPON,  0, 1, "(.*) tried to leave", false},
#    {WEAPON, 14, 1, "(.*) was squished", false},
#    {WEAPON,  0, 1, "(.*) suicides", false},
#    {WEAPON,  6, 1, "(.*) tries to put the pin back in", false},
#    {WEAPON,  7, 1, "(.*) becomes bored with life", false},
#    {WEAPON,  7, 1, "(.*) discovers blast radius", false},
#    {WEAPON, 13, 1, "(.*) electrocutes himself.", false},
#    {WEAPON, 13, 1, "(.*) electrocutes herself.", false},
#    {WEAPON, 13, 1, "(.*) discharges into the slime", false},
#    {WEAPON, 13, 1, "(.*) discharges into the lava", false},
#    {WEAPON, 13, 1, "(.*) discharges into the water", false},
#    {WEAPON, 13, 1, "(.*) heats up the water", false},
#    {WEAPON, 16, 1, "(.*) squished a teammate", false},
#    {WEAPON, 16, 1, "(.*) mows down a teammate", false},
#    {WEAPON, 16, 1, "(.*) checks his glasses", false},
#    {WEAPON, 16, 1, "(.*) checks her glasses", false},
#    {WEAPON, 16, 1, "(.*) gets a frag for the other team", false},
#    {WEAPON, 16, 1, "(.*) loses another friend", false},
#    {WEAPON,  1, 2, "(.*) was ax-murdered by (.*)", false},
#    {WEAPON,  2, 2, "(.*) was lead poisoned by (.*)", false},
#    {WEAPON,  2, 2, "(.*) chewed on (.*)'s boomstick", false},
#    {WEAPON,  3, 2, "(.*) ate 8 loads of (.*)'s buckshot", false},
#    {WEAPON,  3, 2, "(.*) ate 2 loads of (.*)'s buckshot", false},
#    {WEAPON,  4, 2, "(.*) was body pierced by (.*)", false},
#    {WEAPON,  4, 2, "(.*) was nailed by (.*)", false},
#    {WEAPON,  5, 2, "(.*) was perforated by (.*)", false},
#    {WEAPON,  5, 2, "(.*) was punctured by (.*)", false},
#    {WEAPON,  5, 2, "(.*) was ventilated by (.*)", false},
#    {WEAPON,  5, 2, "(.*) was straw-cuttered by (.*)", false},
#    {WEAPON,  6, 2, "(.*) eats (.*)'s pineapple", false},
#    {WEAPON,  6, 2, "(.*) was gibbed by (.*)'s grenade", false},
#    {WEAPON,  7, 2, "(.*) was smeared by (.*)'s quad rocket", false},
#    {WEAPON,  7, 2, "(.*) was brutalized by (.*)'s quad rocket", false},
#    {WEAPON,  7, 2, "(.*) rips (.*) a new one", true},
#    {WEAPON,  7, 2, "(.*) was gibbed by (.*)'s rocket", false},
#    {WEAPON,  7, 2, "(.*) rides (.*)'s rocket", false},
#    {WEAPON,  8, 2, "(.*) accepts (.*)'s shaft", false},
#    {WEAPON,  9, 2, "(.*) was railed by (.*)", false},
#    {WEAPON, 12, 2, "(.*) was telefragged by (.*)", false},
#    {WEAPON, 14, 2, "(.*) squishes (.*)", true},
#    {WEAPON, 13, 2, "(.*) accepts (.*)'s discharge", false},
#    {WEAPON, 13, 2, "(.*) drains (.*)'s batteries", false},
#    {WEAPON,  8, 2, "(.*) gets a natural disaster from (.*)", false},

	#DEFINE OBITUARY	PLAYER_DEATH	DROWN				" sleeps with the fishes"
	#DEFINE OBITUARY	PLAYER_DEATH	DROWN				" sucks it down"
	#DEFINE OBITUARY	PLAYER_DEATH	SLIME				" gulped a load of slime"
	#DEFINE OBITUARY	PLAYER_DEATH	SLIME				" can't exist on slime alone"
	#DEFINE OBITUARY	PLAYER_DEATH	LAVA				" burst into flames"
	#DEFINE OBITUARY	PLAYER_DEATH	LAVA				" turned into hot slag"
	#DEFINE OBITUARY	PLAYER_DEATH	LAVA				" visits the Volcano God"

	#DEFINE OBITUARY	PLAYER_DEATH	FALL				" cratered"
	#DEFINE OBITUARY	PLAYER_DEATH	FALL				" fell to his death"
	#DEFINE OBITUARY	PLAYER_DEATH	FALL				" fell to her death"
	#DEFINE OBITUARY	PLAYER_DEATH	TRAP				" blew up"
	#DEFINE OBITUARY	PLAYER_DEATH	TRAP				" was spiked"
	#DEFINE OBITUARY	PLAYER_DEATH	TRAP				" was zapped"
	#DEFINE OBITUARY	PLAYER_DEATH	TRAP				" ate a lavaball"

	#DEFINE OBITUARY	X_TEAMKILLED_UNKNOWN TELEFRAG		" was telefragged by his teammate"
	#DEFINE OBITUARY	X_TEAMKILLED_UNKNOWN TELEFRAG		" was telefragged by her teammate"


	#DEFINE OBITUARY	PLAYER_DEATH	NOWEAPON			" died"
	#DEFINE OBITUARY	PLAYER_DEATH	NOWEAPON			" tried to leave"
	#DEFINE OBITUARY	PLAYER_DEATH	SQUISH				" was squished"

	#DEFINE OBITUARY	PLAYER_SUICIDE	NOWEAPON			" suicides"

	#DEFINE OBITUARY	PLAYER_SUICIDE	GRENADE_LAUNCHER	" tries to put the pin back in"
	#DEFINE OBITUARY	PLAYER_SUICIDE	ROCKET_LAUNCHER		" becomes bored with life"
	#DEFINE OBITUARY	PLAYER_SUICIDE	ROCKET_LAUNCHER		" discovers blast radius"

	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" electrocutes himself"
	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" electrocutes herself"
	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" railcutes himself" // rail dis
	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" railcutes herself" // rail dis
	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" discharges into the slime"
	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" discharges into the lava"
	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" discharges into the water"
	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" heats up the water"

	#DEFINE OBITUARY	X_TEAMKILLS_UNKNOWN SQUISH			" squished a teammate"
	#DEFINE OBITUARY	X_TEAMKILLS_UNKNOWN TEAMKILL		" mows down a teammate"
	#DEFINE OBITUARY	X_TEAMKILLS_UNKNOWN TEAMKILL		" checks his glasses"
	#DEFINE OBITUARY	X_TEAMKILLS_UNKNOWN TEAMKILL		" checks her glasses"
	#DEFINE OBITUARY	X_TEAMKILLS_UNKNOWN TEAMKILL		" gets a frag for the other team"
	#DEFINE OBITUARY	X_TEAMKILLS_UNKNOWN TEAMKILL		" loses another friend"

	#DEFINE OBITUARY	X_TEAMKILLED_UNKNOWN STOMP			" was crushed by his teammate" // ktpro stomp tk
	#DEFINE OBITUARY	X_TEAMKILLED_UNKNOWN STOMP			" was crushed by her teammate" // ktpro stomp tk
	#DEFINE OBITUARY	X_TEAMKILLED_UNKNOWN STOMP			" was jumped by his teammate"  // ktx addon for ktpro stomp tk
	#DEFINE OBITUARY	X_TEAMKILLED_UNKNOWN STOMP			" was jumped by her teammate"  // ktx addon for ktpro stomp tk

	#DEFINE OBITUARY	X_FRAGGED_BY_Y	STOMP				" softens "   "'s fall" // ktpro stomp kill
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	STOMP				" softens "   "' fall" // ktpro stomp kill
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	STOMP				" tried to catch "      // ktpro stomp kill
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	STOMP				" was crushed by "      // ktpro stomp kill
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	STOMP				" was jumped by "       // ktpro stomp kill
	#DEFINE OBITUARY	X_FRAGS_Y		STOMP				" stomps "              // ktpro stomp kill
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	STOMP				" was literally stomped into particles by " // KTX instagib

	#DEFINE OBITUARY	X_FRAGGED_BY_Y	AXE					" was ax-murdered by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_SHOTGUN			" was lead poisoned by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	SHOTGUN				" chewed on " "'s boomstick"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	SHOTGUN				" chewed on " "' boomstick"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_SUPER_SHOTGUN		" ate 8 loads of "   "'s buckshot"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_SUPER_SHOTGUN		" ate 8 loads of "   "' buckshot"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	SUPER_SHOTGUN		" ate 2 loads of "   "'s buckshot"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	SUPER_SHOTGUN		" ate 2 loads of "   "' buckshot"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	NAILGUN				" was body pierced by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	NAILGUN				" was nailed by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	SUPER_NAILGUN		" was perforated by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	SUPER_NAILGUN		" was punctured by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	SUPER_NAILGUN		" was ventilated by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_SUPER_NAILGUN		" was straw-cuttered by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	GRENADE_LAUNCHER	" eats " "'s pineapple"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	GRENADE_LAUNCHER	" eats " "' pineapple"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	GRENADE_LAUNCHER	" was gibbed by " "'s grenade"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	GRENADE_LAUNCHER	" was gibbed by " "' grenade"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_ROCKET_LAUNCHER	" was smeared by "   "'s quad rocket"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_ROCKET_LAUNCHER	" was smeared by "   "' quad rocket"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_ROCKET_LAUNCHER	" was brutalized by " "'s quad rocket"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_ROCKET_LAUNCHER	" was brutalized by " "' quad rocket"
	#DEFINE OBITUARY	X_FRAGS_Y		Q_ROCKET_LAUNCHER	" rips " " a new one"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	ROCKET_LAUNCHER		" was gibbed by " "'s rocket"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	ROCKET_LAUNCHER		" was gibbed by " "' rocket"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	ROCKET_LAUNCHER		" rides " "'s rocket"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	ROCKET_LAUNCHER		" rides " "' rocket"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	LIGHTNING_GUN		" accepts "  "'s shaft"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	LIGHTNING_GUN		" accepts "  "' shaft"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_LIGHTNING_GUN		" gets a natural disaster from "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	AXE					" was axed to pieces by " // KTX instagib
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	COIL_GUN			" was instagibbed by " // KTX instagib

	#DEFINE OBITUARY	X_FRAGGED_BY_Y	RAIL_GUN			" was railed by "		//for dmm8

	#DEFINE OBITUARY	X_FRAGGED_BY_Y	TELEFRAG			" was telefragged by "
	#DEFINE OBITUARY	X_FRAGS_Y		SQUISH				" squishes "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	DISCHARGE			" accepts "  "'s discharge"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	DISCHARGE			" accepts "  "' discharge"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	DISCHARGE			" drains "   "'s batteries"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	DISCHARGE			" drains "   "' batteries"



# TODO  telefrag after kill
# 1480090073 <-> Onanim was perforated by SHAROK
# 1480090074 <-> SHAROK was telefragged by Onanim

# TODO wasted backgroud
# <div style="background: url('wasted2.jpg')">


# TODO for playTime
# TEAM PLAY:
# 1496323356 <-> dinoel dropped
# 1496323356 <-> dinoel left the game with 0 frags
# 1496323356 <-> Client dinoel removed
#
# 1496323415 <-> Client dinoel connected
# 1496323415 <-> dinoel [xep] rejoins the game with 0 frags
#
# sample: multiple_rejoins_teamlog
#
#
# DEATHMATCH:
# 1496675770 <-> dinoel dropped
# 1496675770 <-> dinoel left the game with 11 frags
# 1496675770 <-> Client dinoel removed
#
# 1496675853 <-> Client dinoel connected
# 1496675854 <-> dinoel entered the game
#
# sample: multiple_drop_deathmatch
