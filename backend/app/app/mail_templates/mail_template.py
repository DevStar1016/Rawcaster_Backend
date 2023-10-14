from app import utils
import datetime

today = datetime.date.today()

year = today.year


def mail_content(content):
    message_content = f"""<html>

            <head>
                <title></title>
            </head>

            <body style="padding: 0px; margin: 0px; font-size:20px; ">

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
                                <td style="padding:8px 0px 8px;">Copyright © {year} All Right Reserved by Rawcaster.com</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

            </body>

            </html>"""
    return message_content


sharer_event_style = """<style type="text/css">
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
                    </style>"""


def event_shared(eventCreatorName, coverImg, eventTitle, eventStartTime, meetingUrl):
    html_message = f"""
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
                        Copyright © 2021 All Right Reserved by <a style="text-decoration: none !important;color:#fff !important" href="https://www.rawcaster.com/">Rawcaster.com</a>
                </div>
            </div>

            </body>

            </html>""" 

    return html_message


def event_mail_template(content):
    html_message = f"""<html>
                    <head>
                        <title></title>
                    </head>
                    <body>
                        {content}

                    </body>
                    </html>"""
    return html_message


def welcome_mail():
    html_message = f"""<div style=" width:100%;">
            <div style="width:100%; background:#fff; padding:0; max-width:700px; margin:auto; ">



                <table width="100%" class="deviceWidth" border="0" cellpadding="0" cellspacing="0" align="center"
                    bgcolor="#fff">
                    <tr>
                        <td align="center">
                            <div class="banner" style="padding:0px 5px 0; ">
                                <a id="link" style="color:#000; text-decoration:none;" href="#">
                                    <img width="100%" class="deviceWidth"
                                        src="https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/video_47351684738486.png"
                                        alt="logo" border="0" /></a>
                            </div>

                            <div style="text-align:left; font-family:Verdana, Geneva, Tahoma, sans-serif; margin:20px 1%;">
                                <div style="margin-top:7px; margin-bottom:0px; color:#000; font-size:18px; line-height:27px;">

                                    <div
                                        style="font-size:16px; color:#000; margin:10px 0px; font-family:Verdana, Geneva, Tahoma, sans-serif; text-align:left; line-height:25px;">

                                        <p style="margin:10px 0px;">
                                            Use this <a href="{utils.inviteBaseurl()}firststep">
                                                link</a>
                                            to read first steps to customize your profile :
                                        </p>
                                        <p style="margin:10px 0px;"><a
                                                        href="{utils.inviteBaseurl()}firststep">{utils.inviteBaseurl()}firststep</a>
                                                </p>

                                        <p style="margin:10px 0px;"> You can also watch this <a
                                                href="https://www.youtube.com/watch?v=g-bWRRpCihk">video</a> for a
                                            demo on how to setup your Rawcaster page :</p>
                                        <p style="margin:10px 0px;"><a
                                                        href="https://www.youtube.com/watch?v=g-bWRRpCihk">https://www.youtube.com/watch?v=g-bWRRpCihk</a>
                                                </p>

                                    </div>
                                </div>

                            </div>
                        </td>
                    </tr>
                </table>



            </div>
        </div> """
    return html_message


invite_mail_style = """<style type="text/css">
                    body {
                        width: 100%;
                        margin: 0;
                        padding: 0;
                        -webkit-font-smoothing: antialiased;
                        font-family: "Roboto";
                        background: #eaeced;
                    }

                    @media only screen and (max-width: 640px) {
                        body[yahoo] .deviceWidth {
                            width: 440px !important;
                            padding: 0;
                        }
                    }

                    @media only screen and (max-width: 479px) {
                        body[yahoo] .deviceWidth {
                            width: 280px !important;
                            padding: 0;
                        }
                    }
                </style>"""


def invite_mail(invite_content):
    html_code = f"""<!doctype html>
            <html xmlns="http://www.w3.org/1999/xhtml">

            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                <title>Rawcater-Newsletter</title>
                <link href='http://fonts.googleapis.com/css?family=Pacifico' rel='stylesheet' type='text/css'>
                {invite_mail_style}
            </head>

            <body leftmargin="0" topmargin="0" marginwidth="0" marginheight="0" yahoo="fix"
                style="background:#eaeced; padding: 0;">

            <div style="background-color:#eaeced; width:100%;font-family: Roboto">
                <div style="width:100%; background:#fff; padding:0; max-width:1000px; margin:auto;">

                    <table width="100%" border="0" cellpadding="0" cellspacing="0" align="center">

                        <table width="100%" border="0" cellpadding="0" cellspacing="0" align="center"
                            class="border-complete deviceWidth border-lr ">
                            <tr>
                                <td width="100%" valign="bottom">
                                    <table border="0" width="100%" valign="bottom" cellpadding="0" cellspacing="0"
                                        align="center" class="deviceWidth">
                                        <tr>
                                            <td>
                                                <div
                                                        style="text-align: center; padding: 40px 0px; background: url('https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/video_47651684737724.jpg');
                                                        background-size: cover;">
                                                    <div>
                                                        <img src="https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/video_84071684737613.png" alt="logo"
                                                            style="max-width: 230px; margin:0 auto 10px auto;">
                                                        <p align="center"
                                                        style="color: #fff; text-align: center; max-width: 740px; font-size: 16px;  line-height: 25px;padding: 0 15px; font-weight:300; margin: auto;">
                                                            Hi, I have joined Rawcaster. A one-stop platform for all social media needs. I am asking all my friends and special people to join this platform to make it easier to reach everyone with content, personalized messages, Nuggets, and invitations to participate in my special events. I expect to see you there soon. <a href={invite_content} style="text-transform: uppercase; text-decoration: underline; font-size: 19px; color: #fff; font-weight:500;">Try it free</a></p>
                                                    </div>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>

                        <table width="100%" border="0" style="margin: auto; max-width: 900px;" cellpadding="0" cellspacing="0" align="center"
                            class="border-lr deviceWidth">

                            <tr align="center">
                                <td align="left" style="padding:0 25px;">
                                    <div style="border: 1px solid #E8EAEE; border-radius: 22px; width: 100%; float: left; position: relative;  margin: 40px 0 0 0; background: url('https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/video_64721684737786.png'); background-repeat: no-repeat;
                                        background-position: right top;background-size: 40px;">

                                        <table width="100%" border="0" cellpadding="0" cellspacing="0" align="center"
                                            class="border-lr deviceWidth">
                                            <tr>
                                                <td class="center">

                                                    <table width="400px" border="0" cellpadding="0" cellspacing="0" align="left"
                                                        class="deviceWidth">

                                                        <tr>
                                                            <td align="left" style="line-height: 0;">
                                                                <a href="#">
                                                                    <img src="https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/video_89491684737931.png" width="100%" border="0"
                                                                        class="deviceWidth" />
                                                                </a>
                                                            </td>
                                                        </tr>

                                                    </table>

                                                    <table width="400px" border="0" cellpadding="0" cellspacing="0"
                                                        align="right" class="deviceWidth">
                                                        <tr>
                                                            <td align="left">
                                                                <div style="margin-top:30px;float: left;">
                                                                    <ul style="padding-left: 10px;">
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 89%; float: left; line-height: 25px;font-weight: 400;">
                                                                                Radio/TV style talk-show events</p>
                                                                        </li>
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 89%; float: left; line-height: 25px;font-weight: 400;">
                                                                                Participants in listen-only mode</p>
                                                                        </li>
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 89%; float: left; line-height: 25px;font-weight: 400;">
                                                                                Live interaction with participants</p>
                                                                        </li>
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 89%; float: left; line-height: 25px;font-weight: 400;">
                                                                                Host with a panel of speakers</p>
                                                                        </li>
                                                                    </ul>
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td align="left" style="padding:0 25px;">
                                    <div style="border: 1px solid #E8EAEE; border-radius: 22px; width: 100%; float: left; position: relative;   margin: 40px 0 0 0;
                                        background: url('https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/video_64721684737786.png');
                                        background-repeat: no-repeat;
                                        background-position: left top;background-size: 40px;">

                                        <table width="100%" border="0" cellpadding="0" cellspacing="0" align="center"
                                            class="border-lr deviceWidth">
                                            <tr>
                                                <td class="center">
                                                    <table width="400px" border="0" cellpadding="0" cellspacing="0"
                                                        align="right" class="deviceWidth">

                                                        <tr>
                                                            <td align="left" style="line-height: 0;">
                                                                <a href="#">
                                                                    <img src="https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/video_63251684738098.png" width="100%" border="0"
                                                                        class="deviceWidth" />
                                                                </a>
                                                            </td>
                                                        </tr>

                                                    </table>

                                                    <table width="400px" border="0" cellpadding="0" cellspacing="0"
                                                        align="right" class="deviceWidth">
                                                        <tr>
                                                            <td align="left">
                                                                <div style="margin-top:30px;float: left;">
                                                                    <ul style="padding-left: 10px;">
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 90%; float: left; line-height: 25px;font-weight: 400">
                                                                                End-to-end encrypted live conversations</p>
                                                                        </li>
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 90%; float: left; line-height: 25px;font-weight: 400">
                                                                                Video calls</p>
                                                                        </li>
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 90%; float: left; line-height: 25px;font-weight: 400">
                                                                                Audio calls</p>
                                                                        </li>
                                                                    </ul>
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td align="left" style="padding:0 25px;">
                                    <div style="border: 1px solid #E8EAEE; border-radius: 22px; width: 100%; float: left; position: relative;  margin: 40px 0 0 0; background: url('https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/video_64721684737786.png'); background-repeat: no-repeat;background-repeat: no-repeat;
                                        background-position: right top;background-size: 40px;">

                                        <table width="100%" border="0" cellpadding="0" cellspacing="0" align="center"
                                            class="border-lr deviceWidth">
                                            <tr>
                                                <td class="center">

                                                    <table width="400px" border="0" cellpadding="0" cellspacing="0" align="left"
                                                        class="deviceWidth">

                                                        <tr>
                                                            <td align="left" style="line-height: 0;">
                                                                <a href="#">
                                                                    <img src="https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/video_77291684738252.png" width="100%" border="0"
                                                                        class="deviceWidth" />
                                                                </a>
                                                            </td>
                                                        </tr>

                                                    </table>

                                                    <table width="400px" border="0" cellpadding="0" cellspacing="0"
                                                        align="right" class="deviceWidth">
                                                        <tr>
                                                            <td align="left">
                                                                <div style="margin-top:30px;float: left;">
                                                                    <ul style="padding-left: 10px;">
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 90%; float: left; line-height: 25px;font-weight: 400">
                                                                                Host a virtual meeting with anyone anywhere</p>
                                                                        </li>
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 90%; float: left; line-height: 25px;font-weight: 400">
                                                                                One-on-one or one-to-many video conference</p>
                                                                        </li>
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 90%; float: left; line-height: 25px;font-weight: 400">
                                                                                Break-out rooms</p>
                                                                        </li>
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 90%; float: left; line-height: 25px;font-weight: 400">
                                                                                Schmoozing</p>
                                                                        </li>
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 90%; float: left; line-height: 25px;font-weight: 400">
                                                                                Voting</p>
                                                                        </li>
                                                                    </ul>
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td align="left" style="padding:0 25px;">
                                    <div style="border: 1px solid #E8EAEE; border-radius: 22px; width: 100%; float: left; position: relative;  margin: 40px 0 0 0; background: url('https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/video_64721684737786.png'); background-repeat: no-repeat;background-repeat: no-repeat;
                                        background-position: left top;background-size: 40px;">

                                        <table width="100%" border="0" cellpadding="0" cellspacing="0" align="center"
                                            class="border-lr deviceWidth">
                                            <tr>
                                                <td class="center">

                                                    <table width="400px" border="0" cellpadding="0" cellspacing="0"
                                                        align="right" class="deviceWidth">

                                                        <tr>
                                                            <td align="left" style="line-height: 0;">
                                                                <a href="#">
                                                                    <img src="https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/video_45881684738343.png" width="100%" border="0"
                                                                        class="deviceWidth" />
                                                                </a>
                                                            </td>
                                                        </tr>

                                                    </table>

                                                    <table width="400px" border="0" cellpadding="0" cellspacing="0"
                                                        align="right" class="deviceWidth">
                                                        <tr>
                                                            <td align="left">
                                                                <div style="margin-top:30px;float: left;">
                                                                    <ul style="padding-left: 10px;">
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 90%; float: left; line-height: 25px;font-weight: 400">
                                                                                Post contents to fans, public or a connection
                                                                            </p>
                                                                        </li>
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 90%; float: left; line-height: 25px;font-weight: 400">
                                                                                Connect with images including videos and
                                                                                pictures</p>
                                                                        </li>
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 90%; float: left; line-height: 25px;font-weight: 400">
                                                                                Ability to download post</p>
                                                                        </li>
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 90%; float: left; line-height: 25px;font-weight: 400">
                                                                                Ability to edit posts</p>
                                                                        </li>
                                                                    </ul>
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td align="left" style="padding:0 25px;">
                                    <div style="border: 1px solid #E8EAEE; border-radius: 22px; width: 100%; float: left; position: relative;  margin: 40px 0; background: url('https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/video_64721684737786.png'); background-repeat: no-repeat;background-repeat: no-repeat;
                                        background-position: right top;background-size: 40px;">

                                        <table width="100%" border="0" cellpadding="0" cellspacing="0" align="center"
                                            class="border-lr deviceWidth">
                                            <tr>
                                                <td class="center">

                                                    <table width="400px" border="0" cellpadding="0" cellspacing="0" align="left"
                                                        class="deviceWidth">

                                                        <tr>
                                                            <td align="left" style="line-height: 0;">
                                                                <a href="#">
                                                                    <img src="https://rawcaster.s3.us-west-2.amazonaws.com/nuggets/video_60581684738435.png" width="100%" border="0"
                                                                        class="deviceWidth" />
                                                                </a>
                                                            </td>
                                                        </tr>

                                                    </table>

                                                    <table width="400px" border="0" cellpadding="0" cellspacing="0"
                                                        align="right" class="deviceWidth">
                                                        <tr>
                                                            <td align="left">
                                                                <div style="margin-top:30px;float: left;">
                                                                    <ul style="padding-left: 10px;">
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 90%; float: left; line-height: 25px;font-weight: 400">
                                                                                Go live with a click of a button</p>
                                                                        </li>
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 90%; float: left; line-height: 25px;font-weight: 400">
                                                                                Live stream a concert, show or any event around
                                                                                you</p>
                                                                        </li>
                                                                        <li
                                                                                style="margin-bottom: 15px; list-style: none; font-size: 16px; font-weight: 500;">
                                                                                <span
                                                                                        style="width: 15px;height: 15px; background: linear-gradient(116.6deg, #F3738B 0.88%, #F99F46 99.2%); display: block; border-radius: 50%;margin-top: 6px; float: left; margin-right: 10px;"></span>
                                                                            <p
                                                                                    style="margin-top: 0;width: 90%; float: left; line-height: 25px;font-weight: 400">Choose your audience
                                                                            </p>
                                                                        </li>
                                                                    </ul>
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                </td>
                        </table>
                        <table style="width: 100%;">
                            <tr>
                                <td>
                                    <center style="width: 100%; float: left;">
                                        <a href={invite_content} style="background: #E26386;border-radius: 12px; padding:21px 23px; color: #fff; font-size: 18px;  border: none; display: block; max-width: 200px; text-decoration: none;">Get Started for Free </a> 
                                    </center>
                                    <p
                                        style="font-size: 16px;margin: 30px auto; text-align: center; opacity: 0.6; color: #1D1C1C; line-height: 22px; width: 100%; float: left;">
                                    If you’d rather not receive future emails of this sort from Rawcaster, <br>
                                    please let us know by email at <a style="color: #000; font-weight: 500;" href="mailto:info@rawcaster.com">info@rawcaster.com</a> <br>
                                    @2021 <a style="text-decoration: none !important;color:#fff !important" href="https://www.rawcaster.com/">Rawcaster.com</a> LLC</p>
                                </td>
                            </tr>
                        </table>

                        </tr>

                    </table>
                </div>
            </div>
            </body>"""

    return html_code
