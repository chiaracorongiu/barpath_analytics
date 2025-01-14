import logging
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required
import matplotlib
import pandas as pd
import numpy as np
matplotlib.use('Agg')
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


movements = ["Bench press", "Squat clean", "Jerk", "Clean Jerk", "Snatch", "Overhead Squat",
             "Power clean", "Power snatch", "Front squat", "Back squat", "Bench", "Deadlift", "Push press", "Pull up"]
group = ["Lower body", "Upper body", "Full body", "Olympic lifts"]


@app.route("/advisor", methods=["GET", "POST"])
@login_required
def advisor():
    action = request.form.get("action")
    if request.method == "POST":
        message_FS = ''
        message_DL = ''
        analyze = request.form.get("analyze")
        action = request.form.get("action")
        if not analyze and not action:
            flash(f"Must provide group")
            return redirect("/advisor")
        if analyze not in group:
            flash(f"Incorrect group")
            return redirect("/advisor")

        if analyze == 'Lower body':
            ref = 'Back squat'
            ref_weight = db.execute(
                "SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement=?", session["user_id"], ref)[0]['max_weight']
            if ref_weight == None:
                flash(f"Must enter back squat PR")
                return redirect("/add_pr")
            FS_theoretical = (85*ref_weight)/100
            FS_inf = (80*ref_weight)/100
            FS_sup = (90*ref_weight)/100
            DL_theoretical = (120*ref_weight)/100
            DL_inf = (115*ref_weight)/100
            DL_sup = (125*ref_weight)/100
            FS = db.execute("SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement='Front squat'", session["user_id"])[
                0]['max_weight']
            if not FS:
                flash(f"Must enter front squat PR")
                return redirect("/add_pr")
            DL = db.execute("SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement='Deadlift'", session["user_id"])[
                0]['max_weight']
            if not DL:
                flash(f"Must enter deadlift PR")
                return redirect("/add_pr")
            headers = ['Front squat', 'Deadlift']
            FS_str = str(FS)
            FS_theo_str = str(FS_theoretical)
            DL_str = str(DL)
            DL_theo_str = str(DL_theoretical)
            if FS_inf > FS:
                message_FS = 'Your front squat is <span style="color: red;">' + FS_str + '</span> VS <span style="color: green;">' + FS_theo_str + \
                    '</span> (85% back squat) ideally. <br>You are probably either lacking strength from your quads or lacking mobility in the front rack position.<br><a target="_blank" href="https://e3rehab.com/how-to-grow-your-quads/" class="btn">Read more about quads strengthening</a><br><a target="_blank" href="https://barbend.com/8-mobility-exercises-and-stretches-to-improve-your-front-squat/" class="btn">Read more on how to improve front squat mobility</a>'
            elif FS > FS_sup:
                message_FS = 'Your front squat is <span style="color: red;">' + FS_str + '</span> VS <span style="color: green;">' + FS_theo_str + \
                    '</span> (85% back squat) ideally. <br>Your lower body is probably quad dominant while lacking strength from your glutes, armstring or lower back.<br><a target="_blank" href="https://www.hss.edu/article_posterior-chain-strengthening.asp" class="btn">Read more about posterior chain strenghtening</a><br> Note: if your front squat is above 85% but your back squat, deadlift, and other posterior chain-dependent lifts are progressing well, this ratio may simply reflect individual biomechanics or a natural strength in front squats. As long as you are injury-free and your performance is balanced across lifts, there’s no urgent need to fix this ratio.'
            else:
                message_FS = 'Well done, your ratio is in the right range'
            if DL_inf > DL:
                message_DL = 'Your deadlift is <span style="color: red;">' + DL_str + '</span> VS <span style="color: green;">' + DL_theo_str + \
                    '</span> (120% back squat) ideally.<br> You are lacking strength from your posterior chain. <br> <a target="_blank" href="https://www.hss.edu/article_posterior-chain-strengthening.asp" class="btn">Read more about posterior chain strenghtening</a>'
            elif DL > DL_sup:
                message_DL = 'Your deadlift is <span style="color: red;">' + DL_str + '</span> VS <span style="color: green;">' + DL_theo_str + \
                    '</span> (120% back squat) ideally. <br>You are probably either lacking strength from your quads or lacking mobility in the squat.<br> <a target="_blank" href="https://e3rehab.com/how-to-grow-your-quads/" class="btn">Read more about quads strengthening</a> <br> <a target="_blank" href="https://ksquaredfitness.com/squat-mobility-exercises/" class="btn">Read more on how to improve back squat mobility</a>'
            else:
                message_DL = 'Well done, your ratio is in the right range'
            messages = [message_FS, message_DL]
            return render_template("advisor.html", analyze=analyze, messages=messages, group=group, headers=headers, ref=ref, ref_weight=ref_weight)

        elif analyze == 'Upper body':
            ref = 'Bench'
            ref_weight = db.execute(
                "SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement=?", session["user_id"], ref)[0]['max_weight']
            if ref_weight == None:
                flash(f"Must enter bench PR")
                return redirect("/add_pr")
            push_theoretical = (85*ref_weight)/100
            push_inf = (80*ref_weight)/100
            push_sup = (90*ref_weight)/100
            traction_theoretical = (90*ref_weight)/100
            traction_inf = (85*ref_weight)/100
            traction_sup = (95*ref_weight)/100
            push = db.execute("SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement='Push press'", session["user_id"])[
                0]['max_weight']
            traction = db.execute(
                "SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement='Pull up'", session["user_id"])[0]['max_weight']
            if not push:
                flash(f"Must enter push press PR")
                return redirect("/add_pr")
            if not traction:
                flash(f"Must enter pull up PR")
                return redirect("/add_pr")
            headers = ['Push press', 'Pull up']
            push_str = str(push)
            push_theo_str = str(push_theoretical)
            traction_str = str(traction)
            traction_theo_str = str(traction_theoretical)
            if push_inf > push:
                message_push = 'Your push press is <span style="color: red;">' + push_str + '</span> VS <span style="color: green;">' + push_theo_str + \
                    '</span> (85% bench) ideally. <br>You are probably either lacking strength from your shoulders/triceps or lacking tecnhique in the lift.<br><a target="_blank" href="https://legionathletics.com/vertical-push-exercises/?srsltid=AfmBOoqEtK6U1JwclbY4zjdJHzE3xI8bxBuVyRDoxlsRUeU1WlY8XYY7" class="btn">Read more about vertical press strengthening</a><br><a target="_blank" href=https://row.gymshark.com/blog/article/best-tricep-exercises class="btn">Read more about triceps strengthening</a><br> <a target="_blank" href="https://www.trainheroic.com/blog/push-press-points-of-performance/" class="btn">Read more about push press technique</a>'
            elif push > push_sup:
                message_push = 'Your push press is <span style="color: red;">' + push_str + '</span> VS <span style="color: green;">' + push_theo_str + \
                    '</span> (85% bench) ideally. <br>If your push press exceeds 85% of your bench press but your bench press is progressing and you’re injury-free, this could reflect individual biomechanics or training priorities. For athletes in sports like weightlifting, CrossFit, or other functional fitness disciplines, a strong push press relative to the bench press is often desirable.'
            else:
                message_push = 'Well done, your ratio is in the right range'
            if traction_inf > traction:
                message_pull = 'Your pull up is <span style="color: red;">' + traction_str + '</span> VS <span style="color: green;">' + traction_theo_str + \
                    '</span> (90% bench) ideally. You are lacking strength from your back.  <br><a target="_blank" class="btn" href="https://simplifaster.com/articles/upper-back-pulling-exercises/">Read more about pulling strenghtening</a>'

            elif traction > traction_sup:
                message_pull = 'Your pull up is <span style="color: red;">' + traction_str + '</span> VS <span style="color: green;">' + traction_theo_str + \
                    '</span> (90% bench) ideally. <br>If your pull up exceeds 90% of your bench press but your bench press is progressing and you’re injury-free, this could reflect individual biomechanics or training priorities. For athletes in sports like weightlifting, CrossFit, or other functional fitness disciplines, a strong pull up relative to the bench press is often desirable.'
            else:
                message_pull = 'Well done, your ratio is in the right range'
            messages = [message_push, message_pull]
            return render_template("advisor.html", analyze=analyze, messages=messages, group=group, headers=headers, ref=ref, ref_weight=ref_weight)

        elif analyze == 'Full body':
            ref = 'Back squat'
            ref_weight = db.execute(
                "SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement=?", session["user_id"], ref)[0]['max_weight']
            if ref_weight == None:
                flash(f"Must enter back squat PR")
                return redirect("/add_pr")
            bench_theoretical = (85*ref_weight)/100
            bench_sup = (90*ref_weight)/100
            bench_inf = (80*ref_weight)/100
            snatch_theoretical = (66*ref_weight)/100
            snatch_inf = (61*ref_weight)/100
            snatch_sup = (71*ref_weight)/100
            clean_theoretical = (80*ref_weight)/100
            clean_inf = (75*ref_weight)/100
            clean_sup = (85*ref_weight)/100
            jerk_theoretical = (84*ref_weight)/100
            jerk_inf = (79*ref_weight)/100
            jerk_sup = (89*ref_weight)/100
            bench = db.execute("SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement=?",
                               session["user_id"], 'Bench press')[0]['max_weight']
            if bench == None:
                flash(f"Must enter bench PR")
                return redirect("/add_pr")
            clean = db.execute("SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement=?",
                               session["user_id"], 'Squat clean')[0]['max_weight']
            print(clean)
            if clean == None:
                flash(f"Must enter clean PR")
                return redirect("/add_pr")

            snatch = db.execute("SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement=?",
                                session["user_id"], 'Snatch')[0]['max_weight']
            if snatch == None:
                flash(f"Must enter snatch PR")
                return redirect("/add_pr")
            jerk = db.execute("SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement=?",
                              session["user_id"], 'Jerk')[0]['max_weight']
            if jerk == None:
                flash(f"Must enter jerk  PR")
                return redirect("/add_pr")

            # bench

            bench_str = str(bench)
            bench_theo_str = str(bench_theoretical)
            if bench_inf > bench:
                message_bench = 'Your bench press is <span style="color: red;">' + bench_str + '</span> VS <span style="color: green;">' + bench_theo_str + \
                    '</span> (85% back squat) ideally. <br>You are probably lacking strength from your pecs and/or triceps and/or deltoïds.<br><a target="_blank" class="btn" href="https://www.kathrynalexander.com/horizontal-pressing-exercises/">Read more about horizontal press strengthening</a>'
            elif bench > bench_sup:
                message_bench = 'Your bench press is <span style="color: red;">' + bench_str + '</span> VS <span style="color: green;">' + bench_theo_str + \
                    '</span> (85% back squat) ideally. <br>Having a bench over 85% of your back squat is not inherently problematic but it is an indicator that you have an imbalance between upper and lower body strength.<br><a target="_blank" class="btn" href="https://www.elitefts.com/education/6-weeks-to-a-bigger-squat/?srsltid=AfmBOoqMIPN0R0qFhmZ1jWjlYJAXW_N0Gq2imkBDZhWyLv6DkmGfsnEg">Read more about increase squat strength</a>'
            else:
                message_bench = 'Well done, your ratio is in the right range'

            # clean

            clean_str = str(clean)
            clean_theo_str = str(clean_theoretical)
            if clean_inf > clean:
                message_clean = 'Your clean is <span style="color: red;">' + clean_str + '</span> VS <span style="color: green;">' + clean_theo_str + \
                    '</span> (80% back squat) ideally. <br>If your ratio front squat/back squat is in the right range, you should work on your clean technique and/or mobility.<br><a target="_blank" class="btn" href="https://www.boxrox.com/squat-clean-technique-tips/">Read more about clean technique</a><br><a target="_blank" href="https://barbend.com/8-mobility-exercises-and-stretches-to-improve-your-front-squat/" class="btn">Read more on how to improve front squat mobility</a>'
            elif clean > clean_sup:
                message_clean = 'Your clean is <span style="color: red;">' + clean_str + '</span> VS <span style="color: green;">' + clean_theo_str + \
                    '</span> (80% back squat) ideally. <br>Having a clean over 80% of your back squat is not inherently problematic—it is often an indicator of great technique and efficiency. However, increasing your absolute strength could unlock even more potential for heavier cleans. Balancing strength and power development is key to long-term progression.<br><a target="_blank" class="btn" href="https://www.elitefts.com/education/6-weeks-to-a-bigger-squat/?srsltid=AfmBOoqMIPN0R0qFhmZ1jWjlYJAXW_N0Gq2imkBDZhWyLv6DkmGfsnEg">Read more about increase squat strength</a>'
            else:
                message_clean = 'Well done, your ratio is in the right range'

            # snatch

            snatch_str = str(snatch)
            snatch_theo_str = str(snatch_theoretical)
            if snatch_inf > snatch:
                message_snatch = 'Your snatch is <span style="color: red;">' + snatch_str + '</span> VS <span style="color: green;">' + snatch_theo_str + \
                    '</span> (66% back squat) ideally. <br>You are probably lacking technique on this lift or lacking overhead mobility.<br><a target="_blank" class="btn" href="https://www.trainheroic.com/blog/how-to-snatch/">Read more about snatch technique</a><br><a target="_blank" class="btn" href="https://thebarbellphysio.com/8-best-drills-unlock-shoulder-mobility/">Read more about overhead mobility</a>'
            elif snatch > snatch_sup:
                message_snatch = 'Your snatch is <span style="color: red;">' + snatch_str + '</span> VS <span style="color: green;">' + snatch_theo_str + \
                    '</span> (66% back squat) ideally. <br>Having a snatch over 80% of your back squat is not inherently problematic—it is often an indicator of great technique and efficiency. However, increasing your absolute strength could unlock even more potential for heavier snatches. Balancing strength and power development is key to long-term progression.<br><a target="_blank" class="btn" href="https://www.elitefts.com/education/6-weeks-to-a-bigger-squat/?srsltid=AfmBOoqMIPN0R0qFhmZ1jWjlYJAXW_N0Gq2imkBDZhWyLv6DkmGfsnEg">Read more about increase squat strength</a>'
            else:
                message_snatch = 'Well done, your ratio is in the right range'

            # jerk

            jerk_str = str(jerk)
            jerk_theo_str = str(jerk_theoretical)
            if jerk_inf > jerk:
                message_jerk = 'Your jerk is <span style="color: red;">' + jerk_str + '</span> VS <span style="color: green;">' + jerk_theo_str + \
                    '</span> (84% back squat) ideally. <br>You are probably lacking technique on this lift or lacking overhead mobility.<br><a target="_blank" class="btn" href="https://dozerweightlifting.com/articles/the-split-jerk">Read more about jerk technique</a><br><a target="_blank" class="btn" href="https://thebarbellphysio.com/8-best-drills-unlock-shoulder-mobility/">Read more about overhead mobility</a>'
            elif jerk > jerk_sup:
                message_jerk = 'Your jerk is <span style="color: red;">' + jerk_str + '</span> VS <span style="color: green;">' + jerk_theo_str + \
                    '</span> (84% back squat) ideally. <br>Having a jerk over 84% of your back squat is not inherently problematic—it is often an indicator of great technique and efficiency. However, increasing your absolute strength could unlock even more potential for heavier jerks. Balancing strength and power development is key to long-term progression.<br><a target="_blank" class="btn" href="https://www.elitefts.com/education/6-weeks-to-a-bigger-squat/?srsltid=AfmBOoqMIPN0R0qFhmZ1jWjlYJAXW_N0Gq2imkBDZhWyLv6DkmGfsnEg">Read more about increase squat strength</a>'
            else:
                message_jerk = 'Well done, your ratio is in the right range'

            messages = [message_bench, message_clean, message_snatch, message_jerk]
            headers = ['Bench', 'Clean', 'Snatch', 'Jerk']
            return render_template("advisor.html", analyze=analyze, messages=messages, group=group, headers=headers, ref=ref, ref_weight=ref_weight)
        else:
            ref = 'Clean Jerk'
            ref_weight = db.execute(
                "SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement=?", session["user_id"], ref)[0]['max_weight']
            if ref_weight == None:
                flash(f"Must enter clean and jerk PR")
                return redirect("/add_pr")
            snatch_theoretical = (82.5*ref_weight)/100
            snatch_inf = (77.5*ref_weight)/100
            snatch_sup = (87.5*ref_weight)/100
            clean_theoretical = (102.5*ref_weight)/100
            clean_inf = (97.5*ref_weight)/100
            clean_sup = (107.5*ref_weight)/100
            pclean_theoretical = (85*ref_weight)/100
            pclean_inf = (90*ref_weight)/100
            pclean_sup = (80*ref_weight)/100
            psnatch_theoretical = (67.5*ref_weight)/100
            psnatch_inf = (62.5*ref_weight)/100
            psnatch_sup = (72.5*ref_weight)/100
            fs_theoretical = (110*ref_weight)/100
            fs_inf = (105*ref_weight)/100
            fs_sup = (115*ref_weight)/100
            bs_theoretical = (125*ref_weight)/100
            bs_inf = (120*ref_weight)/100
            bs_sup = (130*ref_weight)/100

            snatch = db.execute("SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement=?",
                                session["user_id"], 'Snatch')[0]['max_weight']
            if snatch == None:
                flash(f"Must enter snatch PR")
                return redirect("/add_pr")
            clean = db.execute("SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement=?",
                               session["user_id"], 'Squat clean')[0]['max_weight']
            if clean == None:
                flash(f"Must enter clean PR")
                return redirect("/add_pr")
            pclean = db.execute("SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement=?",
                                session["user_id"], 'Power clean')[0]['max_weight']
            if pclean == None:
                flash(f"Must enter power celan PR")
                return redirect("/add_pr")
            psnatch = db.execute("SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement=?",
                                 session["user_id"], 'Power snatch')[0]['max_weight']
            if psnatch == None:
                flash(f"Must enter power snatch PR")
                return redirect("/add_pr")
            fs = db.execute("SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement=?",
                            session["user_id"], 'Front squat')[0]['max_weight']
            if fs == None:
                flash(f"Must enter front squat  PR")
                return redirect("/add_pr")
            bs = db.execute("SELECT MAX(data.weight)AS max_weight FROM data WHERE user_id=? AND movement=?",
                            session["user_id"], 'Back squat')[0]['max_weight']
            if bs == None:
                flash(f"Must enter back squat  PR")
                return redirect("/add_pr")

            # snatch

            snatch_str = str(snatch)
            snatch_theo_str = str(snatch_theoretical)
            if snatch_inf > snatch:
                message_snatch = 'Your snatch is <span style="color: red;">' + snatch_str + '</span> VS <span style="color: green;">' + snatch_theo_str + \
                    '</span> (82.5% of clean&jerk) ideally. <br>You are probably lacking technique on this lift or lacking overhead mobility.<br><a target="_blank" class="btn" href="https://www.trainheroic.com/blog/how-to-snatch/">Read more about snatch technique</a><br><a target="_blank" class="btn" href="https://thebarbellphysio.com/8-best-drills-unlock-shoulder-mobility/">Read more about overhead mobility</a>'
            elif snatch > snatch_sup:
                message_snatch = 'Your snatch is <span style="color: red;">' + snatch_str + '</span> VS <span style="color: green;">' + snatch_theo_str + \
                    '</span> (82.5% of clean&jerk) ideally. <br>Having a snatch over 82.5% of your clean and jerk is not inherently problematic—it is often an indicator of great technique and efficiency. However, the clean and jerk relies more on raw strength compared to the snatch, especially in the clean recovery and jerk phases. A weaker clean and jerk might indicate underdeveloped leg strength.<br><a target="_blank" class="btn" href="https://www.elitefts.com/education/6-weeks-to-a-bigger-squat/?srsltid=AfmBOoqMIPN0R0qFhmZ1jWjlYJAXW_N0Gq2imkBDZhWyLv6DkmGfsnEg">Read more about increasing squat strength</a>'
            else:
                message_snatch = 'Well done, your ratio is in the right range'

            # clean

            clean_str = str(clean)
            clean_theo_str = str(clean_theoretical)
            if clean < clean_inf:
                message_clean = 'Your clean is <span style="color: red;">' + clean_str + '</span> VS <span style="color: green;">' + clean_theo_str + \
                    '</span> (102.5% of clean&jerk) ideally. <br>this indicates that your ability to clean the bar is limiting your total clean and jerk performance. In this case, your jerk strength and technique are strong relative to your clean, and improving the clean should be a priority.<br><a target="_blank" class="btn" href="https://www.boxrox.com/squat-clean-technique-tips/">Read more about clean technique</a><br><a target="_blank" class="btn" href="https://j2fit.com/articles/8-front-squat-variations-for-bigger-quads-and-stronger-lifts">Increase front squat strenght</a>'
            elif clean_sup < clean:
                message_clean = 'Your clean is <span style="color: red;">' + clean_str + '</span> VS <span style="color: green;">' + clean_theo_str + \
                    '</span> (102.5% of clean&jerk) ideally. <br>it means that your jerk is significantly underperforming relative to your clean. This imbalance highlights that while your clean strength and technique are sufficient (or even strong), your jerk is a limiting factor in achieving a higher clean and jerk total.<br><a target="_blank" class="btn" href="https://dozerweightlifting.com/articles/the-split-jerk">Read more about jerk technique</a>'
            else:
                message_clean = 'Well done, your ratio is in the right range'

            # power clean

            pclean_str = str(pclean)
            pclean_theo_str = str(pclean_theoretical)
            if pclean_inf > pclean:
                message_pclean = 'Your power clean is <span style="color: red;">' + pclean_str + '</span> VS <span style="color: green;">' + pclean_theo_str + \
                    '</span> (85% of clean&jerk) ideally. <br> It suggests that your ability to lift explosively and efficiently in the power clean is underdeveloped relative to your overall clean and jerk performance. This imbalance can indicate weaknesses in speed, power production, or technique, as well as insufficient strength in certain phases of the lift.<br><a target="_blank" class="btn" href="https://dozerweightlifting.com/articles/the-split-jerk">Get better at power cleans</a>'

            elif pclean > pclean_sup:
                message_pclean = 'Your power clean is <span style="color: red;">' + pclean_str + '</span> VS <span style="color: green;">' + pclean_theo_str + \
                    '</span> (85% of clean&jerk) ideally. <br>This could indicate strengths in explosive power but weaknesses in the full clean, jerk, or both. This issue could also be that you are not fast enough to drop under the bar.<br><a target="_blank" class="btn" href="https://www.catalystathletics.com/article/1945/Ask-Greg-Moving-Faster-Under-the-Bar/">Read more about dropping faster under the bar</a><br><a target="_blank" class="btn" href="https://dozerweightlifting.com/articles/the-split-jerk">Read more about jerk technique</a>'
            else:
                message_pclean = 'Well done, your ratio is in the right range'
             # power snatch
            psnatch_str = str(psnatch)
            psnatch_theo_str = str(psnatch_theoretical)
            if psnatch_inf > psnatch:
                message_psnatch = 'Your power snatch is <span style="color: red;">' + psnatch_str + '</span> VS <span style="color: green;">' + psnatch_theo_str + \
                    '</span> (67.5% of clean&jerk) ideally. <br>It suggests that your ability to lift explosively and efficiently in the power snatch is underdeveloped relative to your overall clean and jerk performance. This imbalance can indicate weaknesses in speed, power production, or technique, as well as insufficient strength in certain phases of the lift.<br><a target="_blank" class="btn" href="https://www.trainheroic.com/blog/power-snatch/">Get better at power snatch</a>'

            elif psnatch > psnatch_sup:
                message_psnatch = 'Your power snatch is <span style="color: red;">' + psnatch_str + '</span> VS <span style="color: green;">' + psnatch_theo_str + \
                    '</span> (67.5% of clean&jerk) ideally. <br>This could indicate strengths in explosive power but weaknesses in the full clean, jerk, or both.<br><a target="_blank" class="btn" href="https://j2fit.com/articles/8-front-squat-variations-for-bigger-quads-and-stronger-lifts">Increase front squat strenght</a><br><a target="_blank" class="btn" href="https://www.catalystathletics.com/article/1945/Ask-Greg-Moving-Faster-Under-the-Bar/">Read more about dropping faster under the bar</a><br><a target="_blank" class="btn" href="https://dozerweightlifting.com/articles/the-split-jerk">Read more about jerk technique</a>'
            else:
                message_psnatch = 'Well done, your ratio is in the right range'

             # front squat
            fs_str = str(fs)
            fs_theo_str = str(fs_theoretical)
            if fs_inf > fs:
                message_fs = 'Your front squat is <span style="color: red;">' + fs_str + '</span> VS <span style="color: green;">' + fs_theo_str + \
                    '</span> (110% of clean&jerk) ideally. <br>Having a clean and jerk close to your front squat is not inherently problematic—it is often an indicator of great technique and efficiency. However, a weaker clean and jerk might indicate underdeveloped leg strength.<br><a target="_blank" class="btn" href="https://j2fit.com/articles/8-front-squat-variations-for-bigger-quads-and-stronger-lifts">Increase front squat strenght</a>'

            elif fs > fs_sup:
                message_fs = 'Your front squat is <span style="color: red;">' + fs_str + '</span> VS <span style="color: green;">' + fs_theo_str + \
                    '</span> (110% of clean&jerk) ideally. <br>You are probably lacking technique on the clean and jerk or lacking overhead mobility.<br><a target="_blank" class="btn" href="https://www.boxrox.com/squat-clean-technique-tips/">Read more about clean technique</a><br><a target="_blank" class="btn" href="https://dozerweightlifting.com/articles/the-split-jerk">Read more about jerk technique</a><br><a target="_blank" class="btn" href="https://thebarbellphysio.com/8-best-drills-unlock-shoulder-mobility/">Read more about overhead mobility</a>'
            else:
                message_fs = 'Well done, your ratio is in the right range'

             # back squat
            bs_str = str(bs)
            bs_theo_str = str(bs_theoretical)
            if bs_inf > bs:
                message_bs = 'Your back squat is <span style="color: red;">' + bs_str + '</span> VS <span style="color: green;">' + bs_theo_str + \
                    '</span> (125% of clean&jerk) ideally. <br>Having a clean and jerk close to your back squat is not inherently problematic—it is often an indicator of great technique and efficiency. However, a weaker clean and jerk might indicate underdeveloped leg strength.<br><a target="_blank" class="btn" href="https://www.elitefts.com/education/6-weeks-to-a-bigger-squat/?srsltid=AfmBOoqMIPN0R0qFhmZ1jWjlYJAXW_N0Gq2imkBDZhWyLv6DkmGfsnEg">Read more about increasing squat strength</a>'

            elif bs > bs_sup:
                message_bs = 'Your back squat is <span style="color: red;">' + bs_str + '</span> VS <span style="color: green;">' + bs_theo_str + \
                    '</span> (125% of clean&jerk) ideally. <br>You are probably lacking technique on the clean and jerk or lacking overhead mobility.<br><a target="_blank" class="btn" href="https://www.boxrox.com/squat-clean-technique-tips/">Read more about clean technique</a><br><a target="_blank" class="btn" href="https://dozerweightlifting.com/articles/the-split-jerk">Read more about jerk technique</a><br><a target="_blank" class="btn" href="https://thebarbellphysio.com/8-best-drills-unlock-shoulder-mobility/">Read more about overhead mobility</a>'
            else:
                message_bs = 'Well done, your ratio is in the right range'

            messages = [message_snatch, message_clean, message_pclean,
                        message_psnatch, message_fs, message_bs]
            headers = ['Snatch', 'Clean', 'Power clean',
                       'Power snatch', 'Front squat', 'Back squat']
            print(headers)
            return render_template("advisor.html", analyze=analyze, messages=messages, group=group, headers=headers, ref=ref, ref_weight=ref_weight)
    else:
        message_FS = ''
        message_DL = ''
        return render_template("advisor.html", analyze=None, messages=None, group=group, headers=None, ref=None, ref_weight=None)


@app.template_filter('zip')
def zip_filter(a, b):
    return zip(a, b)


@app.route("/")
@login_required
def index():
    objectives = db.execute("""
        SELECT d.movement,
            MAX(d.weight) AS max_weight,
            o.weight AS objective_weight
        FROM data d
        JOIN objective o ON d.movement = o.movement
        WHERE d.user_id = ?
        GROUP BY d.movement
        HAVING o.weight = MAX(o.weight)
    """, session["user_id"])
    return render_template("index.html", objectives=objectives)


@app.route("/add_objective", methods=["GET", "POST"])
@login_required
def add_objective():
    if request.method == "POST":
        # Récupérer les données du formulaire
        movement = request.form.get("movement")
        weight = request.form.get("weight")

        # Validation des entrées utilisateur
        if not movement or not weight:
            flash(f"Must provide movement and weight")
            return redirect("/add_objective")

        if not movement in movements:  # Vérifier si le mouvement est valide
            flash(f"Invalid movement")
            return redirect("/add_objective")

        try:
            weight = float(weight)
            if weight <= 0:
                flash(f"Weight must be a positive number")
                return redirect("/add_objective")
        except ValueError:
            flash(f"Invalid weight format")
            return redirect("/add_objective")

        # Insérer ou mettre à jour l'objectif dans la base de données
        db.execute("""
            INSERT INTO objective (user_id, movement, weight)
            VALUES (?, ?, ?)
        """, session["user_id"], movement, weight)

        # Rediriger l'utilisateur vers la page principale ou une confirmation
        flash(f"Objective for {movement} updated successfully!")
        return redirect("/add_objective")

    # En cas de méthode GET, afficher la page pour ajouter des objectifs
    return render_template("add_objective.html", movements=movements)


@app.route("/add_pr", methods=["GET", "POST"])
@login_required
def add_pr():
    if request.method == "POST":
        # Récupérer les données du formulaire
        movement = request.form.get("movement")
        weight = request.form.get("weight")
        date = request.form.get("date")

        # Validation des entrées utilisateur
        if not movement or not weight:
            flash(f"Must provide movement and weight")
            return redirect("/add_pr")

        if not movement in movements:  # Vérifier si le mouvement est valide
            flash(f"Invalid movement")
            return redirect("/add_pr")

        try:
            weight = float(weight)
            if weight <= 0:
                flash(f"Weight must be a positive number")
                return redirect("/add_pr")
        except ValueError:
            flash(f"Invalid weight format")
            return redirect("/add_pr")

        # Insérer ou mettre à jour l'objectif dans la base de données
        db.execute("""
            INSERT INTO data (user_id, movement, weight, date)
            VALUES (?, ?, ?,?)
        """, session["user_id"], movement, weight, date)

        # Rediriger l'utilisateur vers la page principale ou une confirmation
        flash(f"PR for {movement} updated successfully!")
        return redirect("/add_pr")

    # En cas de méthode GET, afficher la page pour ajouter des objectifs
    return render_template("add_pr.html", movements=movements)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash(f"Must provide username")
            return redirect("/login")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash(f"Must provide password")
            return redirect("/login")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            flash(f"Invalid username or password")
            return redirect("/login")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/evolution", methods=["GET", "POST"])
@login_required
def evolution():
    plot_url = None
    if request.method == "POST":
        movement_evolution = request.form.getlist("movement")
        if not movement_evolution:
            flash(f"Must provide movement")
            return redirect("/evolution")

        if not all(movement in movements for movement in movement_evolution):
            flash(f"Select registered movement")
            return redirect("/evolution")

        placeholders = ','.join('?' for _ in movement_evolution)
        query = f"SELECT movement, weight, date FROM data WHERE user_id = ? AND movement IN ({placeholders})"
        evolution = db.execute(query, session["user_id"], *movement_evolution)

        if len(evolution) == 0:
            return render_template("evolution.html", plot_url=plot_url, movements=movements, message='No data for these movements yet')

        # Prepare data for plotting
        data = {}

        for row in evolution:
            movement = row['movement']
            date = pd.to_datetime(row['date'])  # Convert to pandas datetime
            weight = row['weight']

            if movement not in data:
                data[movement] = {'dates': [], 'weights': []}
            data[movement]['dates'].append(date)
            data[movement]['weights'].append(weight)

        # Create a unified DataFrame with interpolation
        all_dates = sorted(set(date for movement_data in data.values()
                           for date in movement_data['dates']))
        date_range = pd.date_range(start=all_dates[0], end=all_dates[-1])  # Full range of dates
        aligned_data = {}

        for movement, values in data.items():
            # Create a DataFrame for each movement
            df = pd.DataFrame({'date': values['dates'], 'weight': values['weights']})
            df = df.set_index('date').sort_index()  # Sort dates
            df['weight'] = df['weight'].interpolate()  # Interpolate missing values
            aligned_data[movement] = df['weight']

        # Retrieve objective weights
        objectives = db.execute("""
            SELECT d.movement,
                MAX(d.weight) AS max_weight,
                MAX(o.weight) AS objective_weight
            FROM data d
            JOIN objective o ON d.movement = o.movement
            WHERE d.user_id = ?
            GROUP BY d.movement
        """, session["user_id"])
        objective_weights = {row['movement']: row['objective_weight'] for row in objectives}

        # Plot the data
        plt.figure(figsize=(10, 6))

        for movement, weights in aligned_data.items():
            line, = plt.plot(weights.index, weights, marker='o', label=movement)

            # Add objective line
            if movement in objective_weights:
                plt.axhline(
                    y=objective_weights[movement],
                    color=line.get_color(),  # Use the same color as the movement line
                    linestyle='--',
                    label=f'{movement} Objective'
                )
        plt.xlabel('Date')
        plt.ylabel('Weight')
        plt.title('Movement Evolution Over Time')
        plt.legend()
        plt.xticks(rotation=45)

        # Save the plot to a BytesIO object and encode it
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plot_url = base64.b64encode(buf.getvalue()).decode('utf8')
        plt.close()

        return render_template("evolution.html", plot_url=plot_url, movements=movements, message='Graph displayed successfully.')
    else:
        return render_template("evolution.html", plot_url=None, movements=movements, message='No graph to display yet. Please select movements and submit the form.')


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash(f"Must provide username")
            return redirect("/register")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash(f"Must provide password")
            return redirect("/register")
        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            flash(f"Must provide confirmation")
            return redirect("/register")

        username = request.form.get("username")
        confirmation = request.form.get("confirmation")
        password = request.form.get("password")
        if password != confirmation:
            flash(f"Passwords do not match")
            return redirect("/register")

        hash = generate_password_hash(password)
        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        except ValueError:
            flash(f"Username already exists")
            return redirect("/register")
        # Fetch the newly created user_id
        id = db.execute("SELECT id FROM users WHERE username = ?", username)[0]['id']
        for movement in movements:
            db.execute("INSERT INTO objective (user_id, movement,weight) VALUES (?, ?,?)", id, movement, 0)
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")
