"""
Beer & Johnston (Vector Mechanics for Engineers: Statics) Benchmark Presets
"""

PRESETS = {
    "beams": [
        {
            "id": "beer_ch7_overhang",
            "name": "تیر با پیش‌آمدگی، بار گسترده و متمرکز (Beer Ch 7 - Ex 7.2)",
            "description": "تیر سراسری به طول ۱۲ متر دارای کنسول با بار یکنواخت ۲۰ کیلو‌نیوتن بر متر و بار متمرکز ۵۰ کیلو‌نیوتن در انتها",
            "data": {
                "length": 12.0,
                "supports": [
                    {"x": 0.0, "type": "pin"},
                    {"x": 8.0, "type": "roller"}
                ],
                "hinges": [],
                "point_loads": [
                    {"x": 12.0, "fy": -50.0, "fx": 0.0}
                ],
                "moments": [],
                "dist_loads": [
                    {"x1": 0.0, "x2": 8.0, "w1": -20.0, "w2": -20.0}
                ]
            }
        },
        {
            "id": "beer_ch7_triangular",
            "name": "تیر دوسر ساده با بار مثلثی متغیر (Beer Ch 7 - Sample 7.4)",
            "description": "تیر به طول ۶ متر با تکیه‌گاه مفصلی و غلطکی تحت اثر بار مثلثی با شدت صفر تا ۳۰ کیلو‌نیوتن بر متر",
            "data": {
                "length": 6.0,
                "supports": [
                    {"x": 0.0, "type": "pin"},
                    {"x": 6.0, "type": "roller"}
                ],
                "hinges": [],
                "point_loads": [],
                "moments": [],
                "dist_loads": [
                    {"x1": 0.0, "x2": 6.0, "w1": 0.0, "w2": -30.0}
                ]
            }
        },
        {
            "id": "beer_ch7_gerber",
            "name": "تیر مفصل‌دار ژربر (Gerber Beam with Internal Hinge)",
            "description": "تیر پیوسته با مفصل داخلی در موقعیت ۸ متر و تکیه‌گاه گیردار در مبدا",
            "data": {
                "length": 14.0,
                "supports": [
                    {"x": 0.0, "type": "fixed"},
                    {"x": 14.0, "type": "roller"}
                ],
                "hinges": [8.0],
                "point_loads": [
                    {"x": 4.0, "fy": -40.0, "fx": 0.0},
                    {"x": 11.0, "fy": -30.0, "fx": 0.0}
                ],
                "moments": [],
                "dist_loads": []
            }
        }
    ],
    "trusses": [
        {
            "id": "beer_ch6_pratt",
            "name": "خرپای پرات ۶ دهانه (Pratt Truss - Beer Ch 6)",
            "description": "خرپای پل پرات با دهانه ۱۲ متر و ارتفاع ۳ متر، بارگذاری شده در گره‌های پایینی",
            "data": {
                "nodes": [
                    {"x": 0, "y": 0}, {"x": 4, "y": 0}, {"x": 8, "y": 0}, {"x": 12, "y": 0},
                    {"x": 4, "y": 3}, {"x": 8, "y": 3}
                ],
                "elements": [
                    {"node1": 0, "node2": 1}, {"node1": 1, "node2": 2}, {"node1": 2, "node2": 3},
                    {"node1": 4, "node2": 5},
                    {"node1": 0, "node2": 4}, {"node1": 1, "node2": 4},
                    {"node1": 1, "node2": 5}, {"node1": 2, "node2": 5}, {"node1": 3, "node2": 5}
                ],
                "supports": [
                    {"node": 0, "type": "pin"},
                    {"node": 3, "type": "roller"}
                ],
                "loads": [
                    {"node": 1, "fx": 0, "fy": -30000},
                    {"node": 2, "fx": 0, "fy": -30000}
                ]
            }
        },
        {
            "id": "beer_ch6_warren",
            "name": "خرپای وارن با اعضای مایل (Warren Truss)",
            "description": "خرپای وارن متقارن با توزیع کشش و فشار متناوب در قطری‌ها",
            "data": {
                "nodes": [
                    {"x": 0, "y": 0}, {"x": 3, "y": 0}, {"x": 6, "y": 0},
                    {"x": 1.5, "y": 2.598}, {"x": 4.5, "y": 2.598}
                ],
                "elements": [
                    {"node1": 0, "node2": 1}, {"node1": 1, "node2": 2},
                    {"node1": 3, "node2": 4},
                    {"node1": 0, "node2": 3}, {"node1": 1, "node2": 3},
                    {"node1": 1, "node2": 4}, {"node1": 2, "node2": 4}
                ],
                "supports": [
                    {"node": 0, "type": "pin"},
                    {"node": 2, "type": "roller"}
                ],
                "loads": [
                    {"node": 1, "fx": 0, "fy": -20000}
                ]
            }
        }
    ],
    "vectors": [
        {
            "id": "beer_ch2_cables_3d",
            "name": "تعادل نقطه مادی در فضا با ۳ کابل (Beer Ch 2 - Sample 2.9)",
            "description": "حلقه معلق بار ۱۶۰۰ نیوتن که توسط ۳ کابل به دیوار و نقاط تکیه‌گاهی متصل شده است",
            "data": {
                "cables": [
                    {"name": "کابل AB", "origin": [0, 0, 0], "target": [-1.2, 2.0, -0.8]},
                    {"name": "کابل AC", "origin": [0, 0, 0], "target": [1.5, 2.0, -0.6]},
                    {"name": "کابل AD", "origin": [0, 0, 0], "target": [0.0, 2.0, 1.2]}
                ],
                "applied_load": {"fx": 0.0, "fy": -1600.0, "fz": 0.0}
            }
        }
    ],
    "centroids": [
        {
            "id": "beer_ch5_t_section",
            "name": "مقطع مرکب T شکل با سوراخ دایره‌ای (Beer Ch 5)",
            "description": "جان و بال تیر T شکل به همراه بازشو توخالی دایره‌ای در مرکز",
            "data": {
                "shapes": [
                    {"type": "rectangle", "x": 40, "y": 0, "w": 20, "h": 120, "subtract": False},
                    {"type": "rectangle", "x": 0, "y": 120, "w": 100, "h": 20, "subtract": False},
                    {"type": "circle", "xc": 50, "yc": 60, "r": 15, "subtract": True}
                ]
            }
        }
    ],
    "inertia": [
        {
            "id": "beer_ch9_l_angle",
            "name": "نبشی نامساوی L و دایره مور (Beer Ch 9 - Sample 9.8)",
            "description": "محاسبه ممان‌های اینرسی اصلی و رسم دایره مور برای نبشی ۱۰۰ در ۱۵۰ میلیمتر",
            "data": {
                "shapes": [
                    {"type": "rectangle", "x": 0, "y": 0, "w": 100, "h": 20, "subtract": False},
                    {"type": "rectangle", "x": 0, "y": 20, "w": 20, "h": 130, "subtract": False}
                ]
            }
        }
    ],
    "friction": [
        {
            "id": "beer_ch8_slip_tip",
            "name": "بررسی لغزش در برابر واژگونی بلوک (Beer Ch 8 - Sample 8.3)",
            "description": "بلوک مستطیلی تحت بار افقی: آیا قبل از چپ شدن سر می‌خورد یا واژگون می‌شود؟",
            "data": {
                "weight_W": 800.0,
                "width_b": 0.5,
                "height_h": 1.0,
                "force_height_y": 0.7,
                "force_angle_deg": 0.0,
                "incline_theta_deg": 15.0,
                "mu_s": 0.35
            }
        },
        {
            "id": "beer_ch8_capstan",
            "name": "اصطکاک تسمه روی استوانه - فرمول کاپستان (Beer Ch 8)",
            "description": "تسمه با زاویه پیچش ۱۸۰ درجه روی قرقره و ضریب اصطکاک ۰.۳",
            "data": {
                "T1_slack": 100.0,
                "mu": 0.3,
                "wrap_angle_deg": 180.0,
                "drum_radius": 0.25
            }
        }
    ],
    "cables": [
        {
            "id": "beer_ch7_suspension",
            "name": "کابل سهموی پل معلق با بار یکنواخت (Beer Ch 7 - Sample 7.10)",
            "description": "کابل دهانه ۱۰۰ متری با افتادگی ۱۰ متر تحت بار ۵۰ کیلو‌نیوتن بر متر",
            "data": {
                "span_L": 100.0,
                "sag_h": 10.0,
                "w_per_m": 50.0
            }
        }
    ]
}
