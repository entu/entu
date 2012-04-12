# -*- coding: utf-8 -*-

def translation():
    return {
        '':                     '',
        'logout':               'Välju',
        'help':                 'Abi',

        'true':                 'Jah',
        'false':                'Ei',

        'search':               'Otsi',
        'search_found':         'Leiti',
        'search_placeholder':   'Pime kana leiab tera...',

        'public_result_count_0':                'Ei leidnud midagi. Proovi uuesti.',
        'public_result_count_1':                'Leiti üks',
        'public_result_count_more':             'Leiti %s',
        'public_result_count_much_more':        '%(total)s leitud vastest kuvatakse esimesed %(show)s',

        'language':             'Keel',
        'language_english':     'English',
        'language_estonian':    'Eesti keel',

        'menu_bubbles':         'Õpimullid',
        'menu_persons':         'Persoonid',
        'menu_admin':           'Administratsioon',
        'menu_feedback':        'Tagasiside',
        'menu_logout':          'Välju',

        'page_dashboard':       'Armatuurlaud',
        'page_preferences':     'Seaded',
        'page_bubbles':         'Õpimullid',
        'page_persons':         'Persoonid',
        'page_feedback':        'Tagasiside',

        'person_name':                  'Nimi',
        'person_username':              'Kasutajanimi',
        'person_birthdate':             'Sünnikuupäev',
        'person_age':                   'Vanus',
        'person_idcode':                'Isikukood',
        'person_language':              'Keel',
        'person_timezone':              'Ajavöönd',
        'person_gender':                'Sugu',
        'person_gender_male':           'Mees',
        'person_gender_female':         'Naine',
        'person_grades':                'Hinded',
        'person_leeching_bubbles':      'Saaja õpimullides',
        'person_seeding_bubbles':       'Andja õpimullides',
        'person_duplicates':            'Duplikaatide ühendamine',
        'person_duplicates_merge':      'Ühenda valitud...',
        'person_duplicates_next':       'Otsi järgmised...',

        'contact_address':      'Postiaadress',
        'contact_email':        'E-post',
        'contact_phone':        'Telefon',
        'contact_skype':        'Skype',

        'gapps_create_account': 'Loo kasutaja <b>%s</b> ...',
        'gapps_user_exist':     'Kasutaja <b>%s</b> on olemas. Seo see persooniga ...',
        'gapps_nickname_exist': 'Hüüdnimi %(nick)s on olemas. Seo kasutaja <b>%(user)s</b> persooniga ...',
        'gapps_account_created_subject': 'EKA konto',
        'gapps_account_created_message': 'Valmis on saanud sinu uus artun.ee konto.<br /><br />See saab olema sinu esmaseks kontaktiks EKA juures - kooli uudised ja õppeinfo hakkab tulema just sellele aadressile.<br /><br />Esimese sammuna vaheta ajutine parool e-posti kaudu http://gmail.artun.ee<br /><br />Uutele teenustele pääsed ligi<br />E-mail: http://gmail.artun.ee<br />Kalender: http://calendar.artun.ee<br />Dokumendid: http://docs.artun.ee<br />Õppeinfo: http://ois.artun.ee<br />Moodle: http://moodle.artun.ee<br /><br />Su kasutajanimi on %(user)s<br />Sinu ajutine parool on %(password)s<br />E-posti aadress on %(email)s<br /><br />Vaata kindlasti ka KKK-d aadressil http://it.artun.ee/',

        'bubble_add_new':               'Lisa uus',
        'bubble_edit':                  'Muuda',
        'bubble_max_leecher_count':     'Maks. saajate arv',
        'bubble_seeders':               'Andjad',
        'bubble_leecher':               'Saaja',
        'bubble_leechers':              'Saajad',
        'bubble_waitinglist':           'Ootejärjekord',
        'bubble_subbubbles':            'Alammullid',
        'bubble_doc_gradesheet':        'Arvestusleht',
        'bubble_doc_leechers_csv':      'Saajate nimekiri (CSV)',
        'bubble_actions':               'Toimingud',

        'dashboard_grades':     'Minu hinded',

        'open_document':        'Ava dokument',

        'feedback':                             'Tagasiside',
        'feedback_submit':                      'Saada',
        'feedback_mandatory_questions':         '* vastus on nõutud',
        'feedback_unanswered_questionaries':    'Sul on veel vastata %s küsimustiku',


        'application':                          'Sisseastumisavaldus',
        'application_info':                     '',
        'application_signup_desc':              'Sisseastumisavalduse esitamiseks on sul vaja sisse logida. Kui sul on olemas @artun.ee konto, sisene kindlasti sellega. Kui sul seda ei ole, saad sa luua sisseastuja konto. Konto parool saadetakse sulle meilitsi. Kui oled parooli unustanud, siis kasuta uue konto loomise vormi ja sulle saadetakse uus parool.',
        'application_create_account':           'Mul pole kontot ega parooli. Soovin luua konto...',
        'application_send_invitation':                      'Saada kutse meilile',
        'application_email':                'E-post',
        'application_invitation_sent':                      'Kutse saadeti sulle meilile!',
        'application_login_with_password':      'Mul on sisseastuja parool. Sisenen sellega...',
        'application_password':                             'Parool',
        'application_login':                'Sisene',
        'application_login_with_account':       'Mul on @artun.ee konto. Sisenen sellega...',
        'application_signup_mail_subject':      'Sisseastuja konto',
        'application_signup_mail_message':      'Tere tulemast Eesti Kunstiakadeemiasse!<br /><br />Meil on hea meel, et oled otsustanud asuda õppima meie akadeemiasse.<br /><br />Sinu konto Eesti Kunstiakadeemia sisseastumisavalduse esitamiseks on loodud.<br />Konto parool on: <b>%s</b><br /><br />Sisseastumisavalduse saad täita aadressil <a href="http://bubbledu.artun.ee/application">http://bubbledu.artun.ee/application</a><br /><br />Täname!',
        'application_no_more_submissions':      'Lubatud on valida maksimaalselt neli eriala!',
        'application_apply':                    'Kandideerin',
        'application_submit':                   'Esita avaldus',
        'application_submit_success_message':   'Avaldus vastu võetud. Täname!',
        'application_missing_mandatory_fields': 'Punased väljad on kohustuslikud!',
        'application_missing_apply':            'Valige eriala!',
        'application_logout':                   'Välju',

        'message_notify_on_alter_subject':      'Lisati uus %s',

        'rights_caption':                       'Õigused',
        'rights_add':                           'Õiguse lisamiseks otsi persoon...',
        'rights_no_access':                     'Ligipääs puudub',
        'rights_viewer':                        'Võib vaadata',
        'rights_subbubbler':                    'Võib lisada almmulle',
        'rights_editor':                        'Võib muuta',
        'rights_owner':                         'On omanik',

    }
