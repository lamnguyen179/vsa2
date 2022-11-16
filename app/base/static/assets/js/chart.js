/* global Chart:false */

$(function () {
        'use strict';

        var $max_percent_line_chart = $('#max_percent_line_chart');
        var $max_percent_bar_chart_value = $('#max_percent_bar_chart_value');
        var $max_percent_bar_chart_day = $('#max_percent_bar_chart_day');
        var $time_range_max_percent = $('#time_range_max_percent');
        var $select_channel_name = $('#select_channel_name');
        var $btn_show_max_percent_analytic = $('#btn_show_max_percent_analytic');

        $time_range_max_percent.daterangepicker({
            locale: {
                format: 'MM/DD/YYYY'
            },
        });

        let channels;
        // Get channel list
        $.ajax({
            type: "get",
            url: '/get-channel',
            success: function (data, text) {
                if (data.status === SUCCESS) {
                    channels = data['channels'];
                    for (let c in channels) {
                        $select_channel_name.append('<option value="' + channels[c].name + '">' +
                            channels[c].name + '</option>');
                    }
                    $select_channel_name.val(channels[0].name);
                } else {
                    toastr.error(data.msg)
                }

            },
            error: function (request, status, error) {
                console.log(request);
                console.log(error);
            }
        });

        var mode = 'index';
        var intersect = true;

        function chart_options(xlabel, ylabel) {
            let options = {
                maintainAspectRatio: false,
                tooltips: {
                    mode: mode,
                    // intersect: intersect
                },
                hover: {
                    mode: mode,
                    intersect: intersect
                },
                legend: {
                    display: true
                },
                scales: {
                    yAxes: [{
                        gridLines: {
                            display: true,
                        },
                        ticks: {
                            beginAtZero: true,
                        }
                    }],
                    xAxes: [{
                        display: true,
                        gridLines: {
                            display: true
                        },
                        labelString: 'Date'
                    }]
                }

            };
            if (xlabel) {
                options.scales.xAxes[0]['scaleLabel'] = {
                    display: true,
                    labelString: xlabel
                }
            }
            if (ylabel) {
                options.scales.yAxes[0]['scaleLabel'] = {
                    display: true,
                    labelString: ylabel
                }
            }
            return options
        }

        var chart_option_no_axes = chart_options("", "");
        var bar_chart_value_options = chart_options("Max Percent", "Number");
        var max_percent_line_chart = new Chart($max_percent_line_chart, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: chart_option_no_axes
        });

        var max_percent_bar_chart_value = new Chart($max_percent_bar_chart_value, {
            type: 'bar',
            data: {
                labels: ['10', '20', '30', '40', '50', '60', '70', '80', '90', '>100'],
                datasets: []
            },
            options: bar_chart_value_options
        });

        var max_percent_bar_chart_day = new Chart($max_percent_bar_chart_day, {
            type: 'bar',
            data: {
                labels: ['JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'],
                datasets: []
            },
            options: chart_option_no_axes
        });


        function get_max_percent(channel_name, time_range) {
            let data = {
                "channel_name": channel_name,
                "time_range": time_range
            };
            $.ajax({
                type: "post",
                data: data,
                url: '/get-max_percent',
                success: function (data, text) {
                    if (data.status === SUCCESS) {
                        max_percent_line_chart.destroy();
                        max_percent_line_chart = new Chart($max_percent_line_chart, {
                            type: 'line',
                            data: {
                                labels: data['chart_labels'],
                                datasets: [{
                                    label: 'Average',
                                    data: data['data_line_chart']['average'],
                                    fill: false,
                                    borderColor: 'red',
                                    pointBorderColor: 'red',
                                    pointBackgroundColor: 'red'
                                }, {
                                    label: 'P_95',
                                    data: data['data_line_chart']['data_p95'],
                                    fill: false,
                                    borderColor: 'blue',
                                    pointBorderColor: 'blue',
                                    pointBackgroundColor: 'blue'
                                }, {
                                    label: 'P_99',
                                    data: data['data_line_chart']['data_p99'],
                                    fill: false,
                                    borderColor: 'yellow',
                                    pointBorderColor: 'yellow',
                                    pointBackgroundColor: 'yellow'
                                }]
                            },
                            options: chart_option_no_axes
                        });

                        max_percent_bar_chart_value.destroy();
                        max_percent_bar_chart_value = new Chart($max_percent_bar_chart_value, {
                            type: 'bar',
                            data: {
                                labels: ['10', '20', '30', '40', '50', '60', '70', '80', '90', '>100'],
                                datasets: [{
                                    label: 'Max Percent by 10 unit',
                                    data: data['data_bar_chart_by_value'],
                                    fill: false,
                                    backgroundColor: "blue"
                                }]
                            },
                            options: bar_chart_value_options,
                        });

                        max_percent_bar_chart_day.destroy();
                        max_percent_bar_chart_day = new Chart($max_percent_bar_chart_day, {
                            type: 'bar',
                            data: {
                                labels: data['chart_labels'],
                                datasets: [{
                                    label: '20',
                                    data: data['data_bar_chart']['20'],
                                    fill: false,
                                    backgroundColor: "#669999"
                                }, {
                                    label: '40',
                                    data: data['data_bar_chart']['40'],
                                    fill: false,
                                    backgroundColor: "#66ff33"
                                }, {
                                    label: '60',
                                    data: data['data_bar_chart']['60'],
                                    fill: false,
                                    backgroundColor: "#66ccff"
                                }, {
                                    label: '80',
                                    data: data['data_bar_chart']['80'],
                                    fill: false,
                                    backgroundColor: "#ff00ff"
                                }, {
                                    label: '100',
                                    data: data['data_bar_chart']['100'],
                                    fill: false,
                                    backgroundColor: "#ffff00"
                                }, {
                                    label: '120',
                                    data: data['data_bar_chart']['120'],
                                    fill: false,
                                    backgroundColor: "#ff9900"
                                }
                                ]
                            },
                            options: chart_option_no_axes
                        });

                        toastr.success(data.msg);
                    } else {
                        toastr.error(data.msg)
                    }

                },
                error: function (request, status, error) {
                    console.log(request);
                    console.log(error);
                }
            });
        }

        $btn_show_max_percent_analytic.click(function () {
            let channel_name = $select_channel_name.val();
            let time_range = $time_range_max_percent.val();
            get_max_percent(channel_name, time_range)
        });

    }
);
