#!/usr/bin/python
import pdb
import time, sys
from datetime import timedelta, date, datetime
import time
import re
from operator import itemgetter, attrgetter, methodcaller

from optparse import OptionParser,OptionValueError

import fileinput

import ezstatslib

def enum(**enums):
    return type('Enum', (), enums)

possibleWeapons = ["lg", "gl", "rl", "sg", "ssg", "ng", "sng", "axe", "tele"]

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

LOG_TIMESTAMP_DELIMITER = " <-> "

DEFAULT_PLAYER_NAME_MAX_LEN = 10

READ_LINES_LIMIT = 10000
LOGS_INDEX_FILE_NAME = "logs.html"

ERROR_LOG_FILE_NAME = "errors"
SKIPED_LINES_FILE_NAME = "skiped_lines"

HTML_HEADER_STR = "<!DOCTYPE html>\n<html>\n<body>\n<pre>"
HTML_FOOTER_STR = "</pre>\n</body>\n</html>"

HTML_HEADER_SCRIPT_SECTION = \
    "<!DOCTYPE html>\n<html>\n<head>\n" \
    "<title>PAGE_TITLE</title>\n" \
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
    "<script type=\"text/javascript\">\n" \
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
"    $('#highchart_battle_progress').highcharts({\n" \
"        chart: {\n" \
"                zoomType: 'x'\n" \
"            },\n" \
"        title: {\n" \
"            text: 'Battle progress',\n" \
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
"                text: 'Frags'\n" \
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

HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_DIV_TAG = "<div id=\"highchart_battle_progress\" style=\"min-width: 310px; height: 500px; margin: 0 auto\"></div>"

HIGHCHARTS_BATTLE_PROGRESS_GRANULARITY = 4

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
  "  <div class=\"symple-toggle state-closed\" id=\"achievements\">\n" \
  "  <h2 class=\"symple-toggle-trigger \">Achievements</h2>\n" \
  "  <div class=\"symple-toggle-container symple-clearfix\">\n" \
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
  "<link rel='stylesheet' id='symple_shortcode_styles-css'  href='http://demoswpex.wpengine.netdna-cdn.com/symple-shortcodes/wp-content/plugins/symple-shortcodes/shortcodes/css/symple_shortcodes_styles.css?ver=4.5.2' type='text/css' media='all' />\n"

HTML_SCRIPT_SECTION_FOOTER = "</script>\n" + HTML_HEAD_FOLDING_LINKS + "</head>\n<body>\n<pre>"

HTML_FOOTER_NO_PRE = "</body>\n</html>"

HTML_PRE_CLOSE_TAG = "</pre>\n"
  
HTML_BODY_FOLDING_SCRIPT = \
  "<script type='text/javascript' src=\"http://seiyria.com/bootstrap-slider/dependencies/js/jquery.min.js\"></script>\n" \
  "<script type='text/javascript' src=\"http://seiyria.com/bootstrap-slider/js/bootstrap-slider.js\"></script>\n" \
  "<script src=\"https://code.highcharts.com/highcharts.js\"></script>\n" \
  "<script src=\"https://code.highcharts.com/modules/exporting.js\"></script>\n" \
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

BG_COLOR_GRAY  = "#bfbfbf"
BG_COLOR_LIGHT_GRAY = "#e6e6e6"
BG_COLOR_GREEN = "#00ff00"
BG_COLOR_RED   = "#ff5c33"

KILL_STREAK_MIN_VALUE  = 3
DEATH_STREAK_MIN_VALUE = 3

def escapePlayerName(s):
    tokens = ["-", "[", "]", "\\", "^", "$", "*", "."]
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

def readLineWithCheck(f, num):
    line = f.readline()
    num += 1
    if (num > READ_LINES_LIMIT):
        #print "ERROR: too many lines, limit =", READ_LINES_LIMIT
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
#possibleWeapons = ["lg", "gl", "rl", "sg", "ssg", "ng", "sng", "axe"]

    spl = s.split(" ")
    
    if "boomstick" in s: #zrkn chewed on SHAROK's boomstick
        return True, spl[3].split("'")[0], spl[0], "sg"

    elif "was gibbed" in s and "rocket" in s: #rea[rbf] was gibbed by Ilya's rocket
        return True, spl[4].split("'")[0], spl[0], "rl"
    
    elif "was gibbed" in s and "grenade" in s: #zrkn was gibbed by ss's grenade 
        return True, spl[4].split("'")[0], spl[0], "gl"
        
    elif "pineapple" in s: #ss eats rea[rbf]'s pineapple
        return True, spl[2].split("'")[0], spl[0], "gl"
        
    elif "rocket" in s and not "took" in s and not "{rockets}" in s: # zrkn rides EEE's rocket
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
 
    else:
        isKnown = False
        for l in knownSkipLines:
            if l in s:
                isKnown = True

        if not isKnown:
            #print "!!!:", s ,
            logSkipped(s)
        
        return False,"","",""

def suicideDetection(s):
    detectStrs = ["tries to put the pin back in", \
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
                  "can't exist on slime alone", \
                  "gulped a load of slime", \
                  "burst into flames", \
                  "heats up the water"]
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
            return True,"",spl[0]  # only death is increased
        else:
            return True,spl[4].split("\n")[0],spl[0]
    return False,"",""

def teamkillDetection(s):
    detectStrs = ["checks his glasses", \
                  "gets a frag for the other team", \
                  "loses another friend", \
                  "mows down a teammate"]
    for det in detectStrs:
         if det in s:
            return True,s.split( )[0]
    return False,""

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

PowerUpType = enum(UNKNOWN=0, RA=1, YA=2, GA=3, MH=4)
def powerUpTypeToString(pwrType):
    if pwrType == PowerUpType.RA: return "RA"
    if pwrType == PowerUpType.YA: return "YA"    
    if pwrType == PowerUpType.GA: return "GA"
    if pwrType == PowerUpType.MH: return "MH"
    return "NA"

class PowerUp:
    def __init__(self, _type = PowerUpType.UNKNOWN, _time = 0):
        self.type = _type
        self.time = _time
        
    def __str__(self):
        return "%s [%d]" % (powerUpTypeToString(self.type), self.time)

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

    def initPowerUpsByMinutes(self, minutesCnt):        
        self.gaByMinutes = [0 for i in xrange(minutesCnt+1)]
        self.yaByMinutes = [0 for i in xrange(minutesCnt+1)]
        self.raByMinutes = [0 for i in xrange(minutesCnt+1)]
        self.mhByMinutes = [0 for i in xrange(minutesCnt+1)]
        
    def incga(self, minuteNum, time = 0):
        self.gaByMinutes[minuteNum] += 1
        if time != 0:
            self.powerUps.append( PowerUp(PowerUpType.GA, time) )
        
    def incya(self, minuteNum, time = 0):
        self.yaByMinutes[minuteNum] += 1
        if time != 0:
            self.powerUps.append( PowerUp(PowerUpType.YA, time) )
        
    def incra(self, minuteNum, time = 0):
        self.raByMinutes[minuteNum] += 1
        if time != 0:
            self.powerUps.append( PowerUp(PowerUpType.RA, time) )
    
    def incmh(self, minuteNum, time = 0):
        self.mhByMinutes[minuteNum] += 1
        if time != 0:
            self.powerUps.append( PowerUp(PowerUpType.MH, time) )
            
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
    
    def incDeath(self, time, who, whom):
        self.deaths += 1
        self.currentDeathStreak.count += 1
        
        # self.currentDeathStreak.names.append(who)
        self.currentDeathStreak.names += "%s," % (who)
        
        if self.currentDeathStreak.start == 0: self.currentDeathStreak.start = time            
        self.fillStreaks(time)
        
    def incSuicides(self, time):
        self.suicides += 1
        self.currentDeathStreak.count += 1
        
        # self.currentDeathStreak.names.append("SELF")
        self.currentDeathStreak.names += "SELF,"
        
        if self.currentDeathStreak.start == 0: self.currentDeathStreak.start = time            
        self.fillStreaks(time)            
    
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
        return "frags:{0:3d}, kills:{1:3d}, deaths:{2:3d}, suicides:{3:3d}, teamkills:{4:3d}, teamdeaths:{5:3d}, gvn-tkn: {6:5d} - {7:5d} ({8:5d}), ratio:{9:6.3}, eff:{10:6.4}%".format(self.frags(), self.kills, self.deaths, self.suicides, self.teamkills, self.deathsFromTeammates(), self.gvn, self.tkn, self.damageDelta(), self.killRatio(), self.efficiency())
    
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
        rlstr   = "" if not weaponsCheck.is_rl   or totalValue == 0 else "rl:{0:3d}({1:5.4}%), ".format(  self.rl_kills,   (float(self.rl_kills)   / float(totalValue) * 100));
        lgstr   = "" if not weaponsCheck.is_lg   or totalValue == 0 else "lg:{0:3d}({1:6.3}%), ".format(  self.lg_kills,   (float(self.lg_kills)   / float(totalValue) * 100));
        glstr   = "" if not weaponsCheck.is_gl   or totalValue == 0 else "gl:{0:3d}({1:6.3}%), ".format(  self.gl_kills,   (float(self.gl_kills)   / float(totalValue) * 100));
        sgstr   = "" if not weaponsCheck.is_sg   or totalValue == 0 else "sg:{0:3d}({1:6.3}%), ".format(  self.sg_kills,   (float(self.sg_kills)   / float(totalValue) * 100));
        ssgstr  = "" if not weaponsCheck.is_ssg  or totalValue == 0 else "ssg:{0:3d}({1:6.3}%), ".format( self.ssg_kills,  (float(self.ssg_kills)  / float(totalValue) * 100));
        ngstr   = "" if not weaponsCheck.is_ng   or totalValue == 0 else "ng:{0:3d}({1:6.3}%), ".format(  self.ng_kills,   (float(self.ng_kills)   / float(totalValue) * 100));
        sngstr  = "" if not weaponsCheck.is_sng  or totalValue == 0 else "sng:{0:3d}({1:6.3}%), ".format( self.sng_kills,  (float(self.sng_kills)  / float(totalValue) * 100));
        axestr  = "" if not weaponsCheck.is_axe  or totalValue == 0 else "axe:{0:3d}({1:6.3}%), ".format( self.axe_kills,  (float(self.axe_kills)  / float(totalValue) * 100));
        telestr = "" if not weaponsCheck.is_tele or totalValue == 0 else "tele:{0:3d}({1:6.3}%), ".format(self.tele_kills, (float(self.tele_kills) / float(totalValue) * 100));

        resstr = "%s%s%s%s%s%s%s%s%s" % (rlstr, lgstr, glstr, sgstr, ssgstr, ngstr, sngstr, axestr, telestr);
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
        rlstr   = "" if not weaponsCheck.is_rl   or totalValue == 0 else "rl:{0:3d}({1:5.4}%), ".format(  self.rl_deaths,   (float(self.rl_deaths)   / float(totalValue) * 100));
        lgstr   = "" if not weaponsCheck.is_lg   or totalValue == 0 else "lg:{0:3d}({1:6.3}%), ".format(  self.lg_deaths,   (float(self.lg_deaths)   / float(totalValue) * 100));
        glstr   = "" if not weaponsCheck.is_gl   or totalValue == 0 else "gl:{0:3d}({1:6.3}%), ".format(  self.gl_deaths,   (float(self.gl_deaths)   / float(totalValue) * 100));
        sgstr   = "" if not weaponsCheck.is_sg   or totalValue == 0 else "sg:{0:3d}({1:6.3}%), ".format(  self.sg_deaths,   (float(self.sg_deaths)   / float(totalValue) * 100));
        ssgstr  = "" if not weaponsCheck.is_ssg  or totalValue == 0 else "ssg:{0:3d}({1:6.3}%), ".format( self.ssg_deaths,  (float(self.ssg_deaths)  / float(totalValue) * 100));
        ngstr   = "" if not weaponsCheck.is_ng   or totalValue == 0 else "ng:{0:3d}({1:6.3}%), ".format(  self.ng_deaths,   (float(self.ng_deaths)   / float(totalValue) * 100));
        sngstr  = "" if not weaponsCheck.is_sng  or totalValue == 0 else "sng:{0:3d}({1:6.3}%), ".format( self.sng_deaths,  (float(self.sng_deaths)  / float(totalValue) * 100));
        axestr  = "" if not weaponsCheck.is_axe  or totalValue == 0 else "axe:{0:3d}({1:6.3}%), ".format( self.axe_deaths,  (float(self.axe_deaths)  / float(totalValue) * 100));
        telestr = "" if not weaponsCheck.is_tele or totalValue == 0 else "tele:{0:3d}({1:6.3}%), ".format(self.tele_deaths, (float(self.tele_deaths) / float(totalValue) * 100));

        resstr = "%s%s%s%s%s%s%s%s%s" % (rlstr, lgstr, glstr, sgstr, ssgstr, ngstr, sngstr, axestr, telestr);
        if len(resstr) > 2:
            resstr = resstr[:-2]
        return resstr

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
            
    def calculateAchievements(self, matchProgress):
        # LONG_LIVE
        if (len(self.deathStreaks) != 0 and self.deathStreaks[0].start >= self.connectTime + 30):
            self.achievements.append( Achievement(AchievementType.LONG_LIVE, "first time is killed on second %d" % (self.deathStreaks[0].start)) )
            
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
            
        # HORRIBLE_FINISH            
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
                
        # HUNDRED_KILLS
        if self.kills >= 100:
            self.achievements.append( Achievement(AchievementType.HUNDRED_KILLS, "mega killer killed %d enemies" % (self.kills)) )
        
        # HUNDRED_DEATHS
        if self.deaths >= 100:
            self.achievements.append( Achievement(AchievementType.HUNDRED_DEATHS, "was killed %d times" % (self.deaths)) )
        
        # HUNDRED_FRAGS
        if self.frags() >= 100:
            self.achievements.append( Achievement(AchievementType.HUNDRED_FRAGS, "%d frags" % (self.frags())) )
            
        # ALWAYS_THE_FIRST
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

AchievementType = enum( LONG_LIVE  = "Long Live and Prosper",  # the 1st 30 seconds without deaths  DONE
                        SUICIDE_MASTER = "Suicide Master",   # 2 suicides in a row  DONE
                        SUICIDE_KING = "Suicide King",   # 3++ suicides in a row  DONE
                        DEATH_STREAK_PAIN = "What do you know about the pain?...", # 10++ death streak  DONE
                        GREAT_FINISH = "Great Finish", # 2+ places up during the last minute
                        LAST_CHANCE_WINNER = "Finish Guru", # 2+ places up during the last minute and win
                        HORRIBLE_FINISH = "Horrible Finish - finished to play too early", # -2 places up during the last minute  DONE
                        ALWAYS_THE_FIRST = "Always the 1st", # the 1st place from the 1st minute until the finish  DONE tmp img
                        OVERTIME_REASON = "Overtime - 5 minutes of fight more",  # one of who didn't want to give up
                        SECOND_OVERTIME_REASON = "The 2nd overtime!",  # one of who didn't want to give up once more time
                        HUNDRED_KILLS = "More than 100 kills", # 100++ kills  DONE tmp img
                        HUNDRED_DEATHS = "More than 100 deaths", # 100++ deaths  DONE tmp img
                        HUNDRED_FRAGS = "More than 100 frags", # 100++ frags  DONE tmp img
                        RED_ARMOR_EATER = "More that 10 red armors", # 10+ red armors
                        GREEN_ARMOR_EATER = "More that 10 green armors", # 10+ green armors
                        YELLOW_ARMOR_EATER = "More that 10 yellow armors", # 10+ yellow armors
                        MEGA_HEALTH_EATER = "More that 10 mega healths", # 10+ mega healths
                                            )

class Achievement:
    def __init__(self, achtype, extra_info = ""):
        self.achtype = achtype
        self.extra_info = extra_info
        self.count = 1

    def generateHtml(self, size = 150):
        return "<img src=\"%s\" alt=\"%s\" title=\"%s: %s\" style=\"width:%dpx;height:%dpx;\">" % (self.getImgSrc(self.achtype), self.achtype, self.achtype, self.extra_info, size, size)
    
    def getImgSrc(self, achtype):
        if self.achtype == AchievementType.LONG_LIVE:
            return "ezquakestats/img/ach_long_liver.jpg"        
        if self.achtype == AchievementType.SUICIDE_MASTER:
            return "ezquakestats/img/ach_suicide_master.jpg"
        if self.achtype == AchievementType.SUICIDE_KING:
            return "ezquakestats/img/ach_suicide_king.jpg"
        if self.achtype == AchievementType.DEATH_STREAK_PAIN:
            return "ezquakestats/img/ach_death_pain.jpg"
        if self.achtype == AchievementType.HORRIBLE_FINISH:
            return "ezquakestats/img/ach_horrible_finish.jpg"
        
        # temp images
        if self.achtype == AchievementType.ALWAYS_THE_FIRST:
            return "ezquakestats/img/ach_always_the_first.jpg"
        if self.achtype == AchievementType.HUNDRED_KILLS:
            return "ezquakestats/img/ach_100_kills_TMP.jpg"
        if self.achtype == AchievementType.HUNDRED_DEATHS:
            return "ezquakestats/img/ach_100_deaths_TMP.jpg"
        if self.achtype == AchievementType.HUNDRED_FRAGS:
            return "ezquakestats/img/ach_100_frags_TMP.jpg"
        if self.achtype == AchievementType.OVERTIME_REASON:
            return "ezquakestats/img/ach_overtime.jpg"
        
        return "NotImplemented"
    

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
    
    def damageDelta(self):
        return (self.gvn - self.tkn)


class WeaponsCheckRes:
    def __init__(self):
        for weap in possibleWeapons:
            exec("self.is_%s = False" % weap)
        
def getWeaponsCheck(allplayers):
    res = WeaponsCheckRes();
    for pl in allplayers:
        for weap in possibleWeapons:
           weapCheck = False
           exec("weapCheck = (pl.%s_kills != 0) or (pl.%s_deaths != 0);" % (weap, weap))
           if weapCheck:
               exec("res.is_%s = True;" % (weap));
    return res;
            





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

