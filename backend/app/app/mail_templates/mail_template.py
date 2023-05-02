from  app import utils
import datetime

today = datetime.date.today()

year = today.year

def mail_content(content):
    
    message_content=f'''<html>

            <head>
                <title></title>
            </head>

            <body style="padding: 0px; margin: 0px;">

                <div style="background: #edecfa;">
                    <table width="760" align="center"
                        style="background:#fff;-webkit-box-shadow: 0px 0px 11px 0px rgba(201,201,201,1);-moz-box-shadow: 0px 0px 11px 0px rgba(201,201,201,1); box-shadow: 0px 0px 11px 0px rgba(201,201,201,1);">
                            <tr>
                                <th style="padding: 15px 30px; border-bottom: 1px solid #ededed;">
                                    <img src="https://rawcaster.s3.us-west-2.amazonaws.com/profileimage/Image_14971682672044.png"
                                        width="200px" alt="logo" />
                                </th>
                            </tr>
                        </thead>
                        <tbody align="center">
                            <tr>
                                <td style="padding: 50px 0;">
                                    {content}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <table width="760" align="center">
                        <tbody>
                            <tr align="center">
                                <td style="padding:15px 0px 0px;">
                                    <a href="{utils.inviteBaseurl()}termsandconditions"
                                        style="color: #000;">Terms & Conditions</a> |
                                    <a href="{utils.inviteBaseurl()}privacypolicy" style="color: #000;">Privacy
                                        Policy</a>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <table width="100%" align="center" style="background:#007bff; color:#fff; margin-top:21px;">
                        <tbody>
                            <tr align="center">
                                <td style="padding:8px 0px 8px;">Copyright © {year} All Right Reserved by
                                    Rawcaster.com</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

            </body>

            </html>'''
    return message_content

sharer_event_style='''<style type="text/css">
                        body {
                            width: 100%;
                            margin: 0;
                            padding: 0;
                            -webkit-font-smoothing: antialiased;
                            font-family: Georgia, Times, serif;
                            /*                    background: #eaeced;	*/
                        }

                        .ii a[href]:hover {
                            color: #faab1a;
                            text-decoration: none;
                        }

                        table {
                            border-collapse: collapse;
                            text-decoration: none;
                        }

                        img {
                            border: none;
                            display: block;
                        }

                        @media only screen and (max-width: 640px) {
                            body[yahoo] .deviceWidth {
                                width: 440px !important;
                                padding: 0;
                            }

                            body[yahoo] .center {
                                text-align: center !important;
                            }

                            #social-icons {
                                width: 40%;
                            }

                            .title {
                                font-family: Verdana, Geneva, sans-serif;
                                font-size: 18px;
                                margin-bottom: 0;
                            }

                            .quote {
                                font-family: Verdana, Geneva, sans-serif;
                                font-size: 1.5rem;
                                margin: 10px 0;
                            }

                            .bg {
                                background-color: #fff !important;
                            }
                        }

                        @media only screen and (max-width: 479px) {
                            body[yahoo] .deviceWidth {
                                width: 280px !important;
                                padding: 0;
                            }

                            body[yahoo] .center {}

                            #social-icons {
                                width: 60%;
                            }

                            .title {
                                font-family: VOLLKORN-SEMIBOLD;
                                font-size: 14px;
                                margin-bottom: 0;
                            }

                            .quote {
                                font-family: VOLLKORN-ITALIC;
                                font-size: 1rem;
                                margin: 10px 0;
                            }

                            .nopadding {
                                margin: 0 !important;
                            }

                            .bg {
                                background-color: #fff !important;
                            }
                        }

                        /*                @media (min-width:768px) {
                                .banner { padding:5px 15px !important; }
                                }*/

                        a:link {
                            text-decoration: none;
                        }

                        a:visited {
                            text-decoration: none;
                        }

                        a:active {
                            text-decoration: none;
                        }

                        aa:hover {
                            color: yellow
                        }

                        @media only screen and (min-width:650px) {
                            body[yahoo] .visible-xs {
                                display: none !important;
                            }

                            body[yahoo] .top80 {
                                margin-top: 80px;
                                padding-right: 30px !important;
                            }

                            .r50 {
                                margin-right: 30px;
                            }
                        }

                        @media only screen and (max-width:650px) {
                            body[yahoo] .hidden-xs {
                                display: none !important;
                            }

                            .bg {
                                background-color: #fff !important;
                            }
                        }

                        @media (max-width:768px) {
                            .bg {
                                background: #fff !important;
                            }

                            .banner {
                                width: 100%;
                                padding: 0 !important;
                            }
                        }

                        p {
                            color: #000;
                        }
                    </style>'''

def event_shared(eventCreatorName,coverImg,eventTitle,eventStartTime,meetingUrl):

    html_message=f'''
            <!doctype html>
            <html xmlns="http://www.w3.org/1999/xhtml">

            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                <title>Rawcaster Newsletter</title>
                <link href='http://fonts.googleapis.com/css?family=Pacifico' rel='stylesheet' type='text/css'>
                    {sharer_event_style}
                    </head>

            <body leftmargin="0" topmargin="0" marginwidth="0" marginheight="0" yahoo="fix"
                style="font-family: Georgia, Times, serif;">

            <div style=" width:100%; background:#f2f2f2;">
                <div style="text-align: center; padding: 30px 30px;" >
                    <img src="https://rawcaster.s3.us-west-2.amazonaws.com/profileimage/Image_14971682672044.png" alt="logo" style="max-width: 200px; margin: auto;">
                </div>
                <div style="max-width: 500px; margin: auto; font-family:Verdana, Geneva, Tahoma, sans-serif;">
                    You have been invited by <b style="padding: 5px 0;">{eventCreatorName}</b> to an event titled <b style="padding: 5px 0;"><?= $title ?></b>
                </div>
                <div style="width:100%; background:#fff; padding:0; max-width:500px; margin:auto; border-radius: 15px; padding: 20px 0;">

                    <table width="100%" border="0" cellpadding="0" cellspacing="0" align="center">

                        <table width="100%" class="deviceWidth" border="0" cellpadding="0" cellspacing="0" align="center"
                            bgcolor="#fff">
                            <tr>
                                <td align="center">
                                    <div
                                            style="color:#000; font-size:18px; line-height:27px; width: 100%; float: left; text-align:left; font-family:Verdana, Geneva, Tahoma, sans-serif;">
                                        <div
                                                style="font-size:16px; color:#000; font-family:Verdana, Geneva, Tahoma, sans-serif; text-align:left; line-height:20px; width: 100%; text-align: center;">
                                            <img src={coverImg} alt="profile image"
                                                style="max-width: 4000px; border-radius:12px; margin: auto;" align="center">
                                                <p> <b> Rawcaster Event </b></p>
                                                <p><b>{eventStartTime} (UTC)</b></p>
                                            <div style="float: left; width: 100%;text-align: center; ">
                                                <a href="<?= $url ?>"
                                                        style="width: 120px; padding: 10px 20px; background-color: #61366e; border-radius: 30px; color: #fff; font-size: 16px; font-weight: 500; display: block; margin: auto;">Join Event</a>
            <!--                                    <a href="#" style="background: transparent; color: #555; width: 100%; margin: 8px 0 0 0; font-size: 14px; display: block; text-decoration: underline; padding: 10px 0;">Skip</a>-->
                                            </div>
                                        </div>

                                    </div>
                                </td>
                            </tr>
                        </table>
                    </table>
                </div>
                <p
                        style="font-family:Verdana, Geneva, Tahoma, sans-serif; padding: 20px 0; width: 100%; text-align: center; font-size: 14px; margin: 0;">
                    <a href="https://www.rawcaster.com/termsandconditions" style=" color: #555;">Terms & Conditions</a> | <a href="https://www.rawcaster.com/privacypolicy" style=" color: #555;">Privacy
                        Policy</a></p>

                <div>
                    <p
                            style="width: 100%; float: left; padding: 13px 0; text-align: center; background: #007bff; color: #fff; font-family:Verdana, Geneva, Tahoma, sans-serif; margin: 0; font-size: 14px;">
                        Copyright © 2021 All Right Reserved by Rawcaster.com</p>
                </div>
            </div>

            </body>

            </html>'''
    
    return html_message

def event_mail_template(content):
    html_message=f'''<html>
                    <head>
                        <title></title>
                    </head>
                    <body>
                        {content}

                    </body>
                    </html>'''
    return html_message



