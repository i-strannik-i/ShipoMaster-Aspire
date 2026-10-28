# Migrated geometry from the user-supplied ShipoYashchik V2.01.
from math import floor, sin, sqrt, pi, ceil
PI = pi
def vint(x): return int(round(float(x)))
def ЗаменаТчкНаЗапт(x): return float(x)

def ВставитьВырезыПодШипыВСередине(RasstoyanieOtKraya, CntS, Diam_frez, TolshinaPer, Storona, SmeshenieDna, VisotaPer, count=None):
    global DelatKrishku, DelatProrezi, DelatPeregorodki, DnoVPaz, Zazor_vokrug_kvadrata
    CntS = float(CntS)
    i = 0
    d = 0
    d = ActiveDocument
    pass
    s = 0
    sweld = 0
    s = d.Selection.Shapes.First
    i = vint(Storona)
    while i > 0:
        s.Rotate(90)
        i = vint(i - 1)
    VisotaVireza = 0
    N = 0
    if (SmeshenieDna > 0):
        N = count if count is not None else max(1, vint(floor((VisotaPer - SmeshenieDna) / (2 * CntS))))
        if N == 0:
            N = vint(1)
        VisotaVireza = (VisotaPer - SmeshenieDna) / (N * 2 + 1)
    else:
        pass
        N = count if count is not None else max(1, vint(floor((VisotaPer + SmeshenieDna) / (2 * CntS))))
        if N == 0:
            N = vint(1)
        VisotaVireza = (VisotaPer + SmeshenieDna) / (N * 2 + 1)
    crv = 0
    s25 = 0
    pass
    Xc = 0
    Yc = 0
    s_LeftX = 0
    s_BottomY = 0
    Xc = s.LeftX
    s_LeftX = Xc
    if (SmeshenieDna > 0):
        Yc = s.BottomY + SmeshenieDna
    else:
        pass
        Yc = s.BottomY
    s_BottomY = Yc
    s_SizeWidth = 0
    s_SizeWidth = VisotaPer
    Xc = Xc + TolshinaPer
    Yc = Yc + VisotaVireza
    # Receiving mortises need the fit clearance across the material too.
    gap = float(F.Zazor)
    slot_left = Xc - TolshinaPer + RasstoyanieOtKraya - gap
    slot_right = Xc + RasstoyanieOtKraya + gap
    for i in range(vint(0), vint(N - 1)+1):
        if F.joint_locks:
            s25 = ActiveLayer.CreateLockedJoint(slot_left,Yc-gap,slot_right,Yc+VisotaVireza+gap,gap,F.LockInterference,True)
        else:
            s25 = ActiveLayer.CreateRectangle(slot_left, Yc + VisotaVireza + gap, slot_right, Yc - gap)
        s = s25.Trim(s, False, False)
        Yc = Yc + VisotaVireza * 2
    Xc = s_LeftX + TolshinaPer
    Yc = s_BottomY + VisotaVireza
    ofs = 0
    s1 = 0
    s251 = 0
    ofs = sin(45 * PI / 180)
    ofs = (1 - ofs) * Diam_frez / 2
    Yc_save = 0
    if Diam_frez != 0 and not F.joint_locks:
        for i in range(vint(1), vint(N)+1):
            s25 = ActiveLayer.CreateEllipse(slot_left + Diam_frez - ofs, Yc + Diam_frez - ofs - F.Zazor, slot_left - ofs, Yc - ofs - F.Zazor)
            s = s25.Trim(s, False, False)
            s25 = ActiveLayer.CreateEllipse(slot_right - Diam_frez + ofs, Yc + Diam_frez - ofs - F.Zazor, slot_right + ofs, Yc - ofs - F.Zazor)
            s = s25.Trim(s, False, False)
            Yc_save = Yc
            Yc = Yc + VisotaVireza
            s251 = ActiveLayer.CreateEllipse(slot_left + Diam_frez - ofs, Yc + ofs + F.Zazor, slot_left - ofs, Yc - Diam_frez + ofs + F.Zazor)
            s = s251.Trim(s, False, False)
            s251 = ActiveLayer.CreateEllipse(slot_right - Diam_frez + ofs, Yc + ofs + F.Zazor, slot_right + ofs, Yc - Diam_frez + ofs + F.Zazor)
            s = s251.Trim(s, False, False)
            Yc = Yc + VisotaVireza
    i = vint(Storona)
    while i > 0:
        s.Rotate(-90)
        i = vint(i - 1)
    pass

def ВставитьВырезПерегородкиСОднойСтороны(KolichVirezov, Tolshch_Per, Diam_frez, TolshinaMat, TolshinaDna, Storona, Smeshenie):
    global DelatKrishku, DelatProrezi, DelatPeregorodki, DnoVPaz, Zazor_vokrug_kvadrata
    KolichVirezov = vint(KolichVirezov)
    d = 0
    i = 0
    d = ActiveDocument
    pass
    s = 0
    sweld = 0
    s = d.Selection.Shapes.First
    i = vint(Storona)
    while i > 0:
        s.Rotate(90)
        i = vint(i - 1)
    ShirinaVireza = 0
    ShagVirezovPoY = 0
    VisotaVireza = 0
    N = 0
    N = vint(KolichVirezov)
    if N == 0:
        N = vint(1)
    ShirinaVireza = Tolshch_Per
    if (Smeshenie > 0):
        ShagVirezovPoY = (s.SizeHeight - TolshinaMat * 2 - KolichVirezov * Tolshch_Per - Smeshenie) / (KolichVirezov + 1)
    else:
        pass
        ShagVirezovPoY = (s.SizeHeight - TolshinaMat * 2 - KolichVirezov * Tolshch_Per + Smeshenie) / (KolichVirezov + 1)
    crv = 0
    s25 = 0
    pass
    Xc = 0
    Yc = 0
    s_LeftX = 0
    s_BottomY = 0
    VisotaVireza = (s.SizeWidth - TolshinaDna) / 2
    Xc = s.LeftX + VisotaVireza + TolshinaDna
    s_LeftX = Xc
    if (Smeshenie > 0):
        Yc = s.BottomY + Smeshenie + ShagVirezovPoY + TolshinaMat
    else:
        pass
        Yc = s.BottomY + ShagVirezovPoY + TolshinaMat
    s_BottomY = Yc
    Xcr = 0
    Ycr = 0
    s_SizeWidth = 0
    s_SizeWidth = s.SizeWidth
    for i in range(vint(1), vint(N)+1):
        s25 = ActiveLayer.CreateRectangle(Xc, Yc + ShirinaVireza, Xc + VisotaVireza, Yc)
        s = s25.Trim(s, False, False)
        Yc = Yc + ShirinaVireza + ShagVirezovPoY
    ofs = 0
    s1 = 0
    s251 = 0
    s251r = 0
    ofs = sin(45 * PI / 180)
    ofs = (1 - ofs) * Diam_frez / 2
    Xc = s_LeftX + Diam_frez / sqrt(2)
    Yc = s_BottomY + Diam_frez / sqrt(2)
    Xcr = Xc + s_SizeWidth - TolshinaMat * 2
    Yc_save = 0
    if Diam_frez != 0:
        for i in range(vint(1), vint(N)+1):
            s25 = ActiveLayer.CreateEllipse(Xc - Diam_frez + ofs, Yc + ofs, Xc + ofs, Yc - Diam_frez + ofs)
            s = s25.Trim(s, False, False)
            Yc_save = Yc
            Yc = Yc + ShirinaVireza - 2 * Diam_frez / sqrt(2)
            s251 = ActiveLayer.CreateEllipse(Xc - Diam_frez + ofs, Yc + Diam_frez - ofs, Xc + ofs, Yc - ofs)
            s = s251.Trim(s, False, False)
            Yc = Yc + ShagVirezovPoY + 2 * Diam_frez / sqrt(2)
    i = vint(Storona)
    while i > 0:
        s.Rotate(-90)
        i = vint(i - 1)
    pass

def ВставитьВырезСОднойСтороны(CntS, Diam_frez, Tolshina, Storona, Smeshenie, DelKr, count=None):
    global DelatKrishku, DelatProrezi, DelatPeregorodki, DnoVPaz, Zazor_vokrug_kvadrata
    CntS = float(CntS)
    d = 0
    i = 0
    kr = 0
    d = ActiveDocument
    pass
    s = 0
    sweld = 0
    s = d.Selection.Shapes.First
    i = Storona
    while i > 0:
        s.Rotate(90)
        i = i - 1
    выс_шип = 0
    N = 0
    kr = vint(1)
    if DelKr == True:
        kr = vint(2)
    if (Smeshenie > 0):
        N = count if count is not None else max(1, vint(floor((s.SizeHeight - Smeshenie * kr) / (2 * CntS))))
        if N == 0:
            N = vint(1)
        выс_шип = (s.SizeHeight - Smeshenie * kr) / (N * 2 + 1)
    else:
        pass
        N = count if count is not None else max(1, vint(floor((s.SizeHeight + Smeshenie * kr) / (2 * CntS))))
        if N == 0:
            N = vint(1)
        выс_шип = (s.SizeHeight + Smeshenie * kr) / (N * 2 + 1)
    crv = 0
    s25 = 0
    pass
    Xc = 0
    Yc = 0
    s_LeftX = 0
    s_BottomY = 0
    Xc = s.LeftX
    s_LeftX = Xc
    if (Smeshenie > 0):
        Yc = s.BottomY + Smeshenie
    else:
        pass
        Yc = s.BottomY - Smeshenie * (kr - 1)
    s_BottomY = Yc
    s_SizeWidth = 0
    s_SizeWidth = s.SizeWidth
    for i in range(vint(0), vint(N)+1):
        s25 = ActiveLayer.CreateRectangle(Xc, Yc + выс_шип, Xc + Tolshina, Yc)
        s = s25.Trim(s, False, False)
        Yc = Yc + выс_шип * 2
    Xc = s_LeftX + Tolshina
    Yc = s_BottomY + выс_шип
    ofs = 0
    s1 = 0
    s251 = 0
    ofs = sin(45 * PI / 180)
    ofs = (1 - ofs) * Diam_frez / 2
    Yc_save = 0
    if Diam_frez != 0:
        for i in range(vint(1), vint(N)+1):
            s25 = ActiveLayer.CreateEllipse(Xc - Diam_frez + ofs, Yc + ofs, Xc + ofs, Yc - Diam_frez + ofs)
            s = s25.Trim(s, False, False)
            Yc_save = Yc
            Yc = Yc + выс_шип
            s251 = ActiveLayer.CreateEllipse(Xc - Diam_frez + ofs, Yc + Diam_frez - ofs, Xc + ofs, Yc - ofs)
            s = s251.Trim(s, False, False)
            Yc = Yc + выс_шип
    i = Storona
    while i > 0:
        s.Rotate(-90)
        i = i - 1
    pass

def ВставитьШипСОднойСтороны(CntS, Diam_frez, Tolshina, Storona, Smeshenie, SmeshenieNaDno, DelKr, count=None):
    global DelatKrishku, DelatProrezi, DelatPeregorodki, DnoVPaz, Zazor_vokrug_kvadrata
    CntS = float(CntS)
    i = 0
    kr = 0
    d = 0
    d = ActiveDocument
    pass
    s = 0
    sweld = 0
    s = d.Selection.Shapes.First
    i = Storona
    while i > 0:
        s.Rotate(90)
        i = i - 1
    выс_шип = 0
    SmeshenieKrishki = 0
    N = 0
    kr = vint(1)
    if DelKr == True:
        kr = vint(2)
    if (DelatProrezi == True) and (DelKr == False):
        SmeshenieKrishki = SmeshenieNaDno
    else:
        pass
        SmeshenieKrishki = 0
    if (Smeshenie > 0):
        N = count if count is not None else max(1, vint(floor((s.SizeHeight - Smeshenie * kr) / (2 * CntS))))
        выс_шип = (s.SizeHeight - Smeshenie * kr) / (N * 2 + 1)
    else:
        pass
        N = count if count is not None else max(1, vint(floor((s.SizeHeight + Smeshenie * kr) / (2 * CntS))))
        выс_шип = (s.SizeHeight + Smeshenie * kr) / (N * 2 + 1)
    crv = 0
    s25 = 0
    pass
    Xc = 0
    Yc = 0
    s_LeftX = 0
    s_BottomY = 0
    Xc = s.LeftX
    s_LeftX = Xc
    if (Smeshenie > 0):
        Yc = s.BottomY + Smeshenie - SmeshenieKrishki
    else:
        pass
        Yc = s.BottomY - Smeshenie * (kr - 1) + SmeshenieKrishki
    s_BottomY = Yc
    s_SizeWidth = 0
    s_SizeWidth = s.SizeWidth
    Xc = Xc + Tolshina
    Yc = Yc + выс_шип
    # An inset bottom creates enclosed mortises. Preserve their centre and
    # expand both walls; ordinary edge joints retain their nominal depth.
    cross_gap = float(F.Zazor) if SmeshenieNaDno > 0 else 0.0
    slot_left = Xc - Tolshina + SmeshenieNaDno - cross_gap
    slot_right = Xc + SmeshenieNaDno + cross_gap
    for i in range(vint(0), vint(N - 1)+1):
        if F.joint_locks:
            s25 = ActiveLayer.CreateLockedJoint(slot_left,Yc-F.Zazor,slot_right,Yc+выс_шип+F.Zazor,F.Zazor,F.LockInterference,SmeshenieNaDno>0)
        else:
            s25 = ActiveLayer.CreateRectangle(slot_left, Yc + выс_шип + F.Zazor, slot_right, Yc - F.Zazor)
        s = s25.Trim(s, False, False)
        Yc = Yc + выс_шип * 2
    Xc = s_LeftX + Tolshina
    Yc = s_BottomY + выс_шип
    ofs = 0
    s1 = 0
    s251 = 0
    ofs = sin(45 * PI / 180)
    ofs = (1 - ofs) * Diam_frez / 2
    Yc_save = 0
    if Diam_frez != 0 and not F.joint_locks:
        for i in range(vint(1), vint(N)+1):
            s25 = ActiveLayer.CreateEllipse(slot_right - Diam_frez + ofs, Yc + Diam_frez - ofs - F.Zazor, slot_right + ofs, Yc - ofs - F.Zazor)
            s = s25.Trim(s, False, False)
            if (DnoVPaz == True or DelatProrezi == True) and SmeshenieNaDno > 0:
                s25 = ActiveLayer.CreateEllipse(slot_left + Diam_frez - ofs, Yc + Diam_frez - ofs - F.Zazor, slot_left - ofs, Yc - ofs - F.Zazor)
                s = s25.Trim(s, False, False)
            Yc_save = Yc
            Yc = Yc + выс_шип
            s251 = ActiveLayer.CreateEllipse(slot_right - Diam_frez + ofs, Yc + ofs + F.Zazor, slot_right + ofs, Yc - Diam_frez + ofs + F.Zazor)
            s = s251.Trim(s, False, False)
            if (DnoVPaz == True or DelatProrezi == True) and SmeshenieNaDno > 0:
                s251 = ActiveLayer.CreateEllipse(slot_left + Diam_frez - ofs, Yc + ofs + F.Zazor, slot_left - ofs, Yc - Diam_frez + ofs + F.Zazor)
                s = s251.Trim(s, False, False)
            Yc = Yc + выс_шип
    i = Storona
    while i > 0:
        s.Rotate(-90)
        i = i - 1
    pass

def РисуемПрорези(Storona):
    global DelatKrishku, DelatProrezi, DelatPeregorodki, DnoVPaz, Zazor_vokrug_kvadrata
    d = 0
    i = 0
    j = 0
    kr = 0
    d = ActiveDocument
    pass
    s = 0
    sweld = 0
    s = d.Selection.Shapes.First
    i = Storona
    while i > 0:
        s.Rotate(90)
        i = i - 1
    DlinaProrezi = 0
    DlinaPerem = 0
    MezduParal = 0
    KolRyadov = 0
    KolPoShirine = 0
    N = 0
    DlinaProrezi = (s.SizeHeight - (vint(F.ProrKolPoShirine) + 1) * float(F.ProrMezduLin)) / vint(F.ProrKolPoShirine)
    DlinaPerem = float(F.ProrMezduLin)
    KolRyadov = max(1, ceil(float(F.RazmerPror) / float(F.ProrMezduParal)))
    MezduParal = float(F.RazmerPror) / KolRyadov
    KolPoShirine = vint(F.ProrKolPoShirine)
    s25 = 0
    Xc = 0
    Yc = 0
    dY = 0
    s_LeftX = 0
    s_BottomY = 0
    Xc = s.LeftX + F.ProrRasstOtKraya
    s_BottomY = s.BottomY
    for i in range(vint(0), vint(KolRyadov)+1):
        Yc = s_BottomY - 0.01
        for j in range(vint(0), vint(KolPoShirine)+1):
            if ((i / 2 - vint(i / 2)) != 0) and ((j == 0) or (j == KolPoShirine)):
                dY = DlinaProrezi / 2 + DlinaPerem / 2
            else:
                pass
                if j == 0:
                    Yc = Yc + DlinaPerem
                if j == KolPoShirine:
                    dY = 0
                else:
                    pass
                    dY = DlinaProrezi
            if dY > 0:
                s25 = ActiveLayer.CreateLineSegment(Xc, Yc, Xc, Yc + dY + 0.01)
                s = s25.Trim(s, False, False)
            Yc = Yc + dY + DlinaPerem
        Xc = Xc + MezduParal
    i = Storona
    while i > 0:
        s.Rotate(-90)
        i = i - 1
    pass

def РисуемДугу(Storona, SmeschNaDno):
    global DelatKrishku, DelatProrezi, DelatPeregorodki, DnoVPaz, Zazor_vokrug_kvadrata
    d = 0
    i = 0
    j = 0
    kr = 0
    d = ActiveDocument
    pass
    s = 0
    sweld = 0
    s = d.Selection.Shapes.First
    i = Storona
    while i > 0:
        s.Rotate(90)
        i = i - 1
    Radius = 0
    s25 = 0
    Xc = 0
    Yc = 0
    dY = 0
    s_LeftX = 0
    s_BottomY = 0
    Xc = s.LeftX
    if SmeschNaDno == 1:
        Yc = s.BottomY + F.visota / 2 - F.DMaterialDna / 2
    else:
        pass
        Yc = s.BottomY + F.visota / 2 + F.DMaterialDna / 2
    s25 = ActiveLayer.CreateEllipse2(Xc, Yc, (F.visota - F.DMaterialDna) / 2, None, 0, 360)
    s = s25.Weld(s, False, False)
    i = Storona
    while i > 0:
        s.Rotate(-90)
        i = i - 1
    pass

def CommandButton2_Click():
    global DelatKrishku, DelatProrezi, DelatPeregorodki, DnoVPaz, Zazor_vokrug_kvadrata
    if mode != 6:
        SmeschDna = 0
        SmeschKr = 0
        ShipVisota = 0
        ShipDlina = 0
        ShipShirina = 0
        x1 = 0
        x2 = 0
        y1 = 0
        y2 = 0
        MaterialM2 = 0
        DnoM2 = 0
        PeregorodkaM2 = 0
        Zazor_vokrug_kvadrata = 10
        if DnoVPaz == True:
            SmeschDna = float(F.SmeshenieDno)
        else:
            pass
            SmeschDna = 0
        if DelatProrezi == True:
            SmeschKr = float(F.SmeshenieKr)
        else:
            pass
            SmeschKr = 0
        if Application.Documents.Count == 0:
            pass
        pass
        F.shirina = ЗаменаТчкНаЗапт(F.shirina)
        F.visota = ЗаменаТчкНаЗапт(F.visota)
        F.dlinna = ЗаменаТчкНаЗапт(F.dlinna)
        F.dFreza = ЗаменаТчкНаЗапт(F.dFreza)
        F.KolPoVisote = ЗаменаТчкНаЗапт(F.KolPoVisote)
        F.KolPoShirine = ЗаменаТчкНаЗапт(F.KolPoShirine)
        F.KolPoDlinne = ЗаменаТчкНаЗапт(F.KolPoDlinne)
        F.DlinaShipa = ЗаменаТчкНаЗапт(F.DlinaShipa)
        F.dMaterial = ЗаменаТчкНаЗапт(F.dMaterial)
        F.DMaterialDna = ЗаменаТчкНаЗапт(F.DMaterialDna)
        F.Zazor = ЗаменаТчкНаЗапт(F.Zazor)
        F.TolshinaPeregorodok = ЗаменаТчкНаЗапт(F.TolshinaPeregorodok)
        F.VisotaPeregorodok = ЗаменаТчкНаЗапт(F.VisotaPeregorodok)
        ActivePage.SizeHeight = float(F.shirina) + float(F.visota) * 2 + Zazor_vokrug_kvadrata * 4
        ActivePage.SizeWidth = float(F.dlinna) + float(F.visota) * 2 + float(F.visota) * (vint(F.KolPeregorodokPoDline) + vint(F.KolPeregorodokPoShirine)) + Zazor_vokrug_kvadrata * 4 + Zazor_vokrug_kvadrata * (vint(F.KolPeregorodokPoDline) + vint(F.KolPeregorodokPoShirine))
        if F.OptionButton1 == True:
            ShipVisota = F.DlinaShipa
            ShipDlina = F.DlinaShipa
            ShipShirina = F.DlinaShipa
        if F.OptionButton2 == True:
            ShipVisota = float(F.visota) / (float(F.KolPoVisote) * 2 + 1)
            ShipDlina = float(F.dlinna) / (F.KolPoDlinne * 2 + 1)
            ShipShirina = float(F.shirina) / (float(F.KolPoShirine) * 2 + 1)
        x1 = Zazor_vokrug_kvadrata
        y1 = ActivePage.SizeHeight / 2 - float(F.shirina) / 2
        x2 = float(F.visota) + Zazor_vokrug_kvadrata
        y2 = ActivePage.SizeHeight / 2 + float(F.shirina) / 2
        ActiveLayer.CreateRectangle(x1, y1, x2, y2)
        MaterialM2 = MaterialM2 + (float(F.shirina) * float(F.visota))
        if DnoVPaz == True:
            ВставитьШипСОднойСтороны(ShipVisota, float(F.dFreza), float(F.dMaterial), 1, 0, 0, False, count=int(F.KolPoVisote) if F.OptionButton2 else None)
            ВставитьШипСОднойСтороны(ShipVisota, float(F.dFreza), float(F.dMaterial), 3, 0, 0, False, count=int(F.KolPoVisote) if F.OptionButton2 else None)
            ВставитьШипСОднойСтороны(ShipShirina, float(F.dFreza), float(F.DMaterialDna), 2, 0, float(SmeschDna), False, count=int(F.KolPoShirine) if F.OptionButton2 else None)
        else:
            pass
            ВставитьШипСОднойСтороны(ShipVisota, float(F.dFreza), float(F.dMaterial), 1, -float(F.DMaterialDna), 0, DelatKrishku, count=int(F.KolPoVisote) if F.OptionButton2 else None)
            ВставитьШипСОднойСтороны(ShipVisota, float(F.dFreza), float(F.dMaterial), 3, float(F.DMaterialDna), 0, DelatKrishku, count=int(F.KolPoVisote) if F.OptionButton2 else None)
            ВставитьВырезСОднойСтороны(ShipShirina, float(F.dFreza), float(F.DMaterialDna), 2, 0, False, count=int(F.KolPoShirine) if F.OptionButton2 else None)
            if DelatKrishku == True:
                ВставитьВырезСОднойСтороны(ShipShirina, float(F.dFreza), float(F.DMaterialDna), 0, 0, False, count=int(F.KolPoShirine) if F.OptionButton2 else None)
        i = 0
        N = 0
        X_Peregorodki = 0
        Inc_X_Peregorodki = 0
        i = 0
        N = vint(vint(F.KolPeregorodokPoShirine))
        Inc_X_Peregorodki = (float(F.shirina) - 2 * float(F.dMaterial) - vint(F.KolPeregorodokPoShirine) * float(F.TolshinaPeregorodok)) / (vint(F.KolPeregorodokPoShirine) + 1)
        X_Peregorodki = Inc_X_Peregorodki + F.dMaterial
        if DelatPeregorodki == True:
            while i < N:
                if F.OptionButton1 == True:
                    ВставитьВырезыПодШипыВСередине(float(X_Peregorodki), float(F.DlinaShipa), float(F.dFreza), float(F.TolshinaPeregorodok), 3, float(F.DMaterialDna) + float(SmeschDna), float(F.VisotaPeregorodok))
                if F.OptionButton2 == True:
                    ВставитьВырезыПодШипыВСередине(float(X_Peregorodki), (((float(F.visota) - float(SmeschDna)) - float(F.DMaterialDna)) / (floor(F.KolPoVisote) * 2 + 1)), float(F.dFreza), float(F.TolshinaPeregorodok), 3, float(F.DMaterialDna) + float(SmeschDna), float(F.VisotaPeregorodok), count=int(F.KolPoVisote) if F.OptionButton2 else None)
                i = i + 1
                X_Peregorodki = X_Peregorodki + Inc_X_Peregorodki + float(F.TolshinaPeregorodok)
        pass
        x1 = Zazor_vokrug_kvadrata * 2 + float(F.visota)
        y1 = Zazor_vokrug_kvadrata * 3 + float(F.visota) + float(F.shirina)
        if DelatProrezi == True:
            x1 = x1 + F.visota / 2
            y1 = y1 + Zazor_vokrug_kvadrata
        x2 = x1 + float(F.dlinna)
        y2 = y1 + float(F.visota)
        ActiveLayer.CreateRectangle(x1, y1, x2, y2)
        MaterialM2 = MaterialM2 + (float(F.dlinna) * float(F.visota))
        if DelatProrezi == True:
            ВставитьВырезСОднойСтороны(ShipVisota, float(F.dFreza), F.dMaterial, 0, F.DMaterialDna, DelatKrishku, count=int(F.KolPoVisote) if F.OptionButton2 else None)
            ВставитьВырезСОднойСтороны(ShipDlina, float(F.dFreza), F.DMaterialDna, 3, 0, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
            РисуемДугу(2, 1)
            Inc_X_Peregorodki = float(F.dlinna) - 2 * float(F.dMaterial)
            X_Peregorodki = Inc_X_Peregorodki + F.dMaterial
            ВставитьВырезыПодШипыВСередине(float(X_Peregorodki), ((float(F.visota) - float(SmeschDna)) / (F.KolPoVisote * 2 + 1)), float(F.dFreza), F.dMaterial, 0, float(F.DMaterialDna) + float(SmeschDna), F.VisotaPeregorodok, count=int(F.KolPoVisote) if F.OptionButton2 else None)
        else:
            pass
            if DnoVPaz == True:
                ВставитьВырезСОднойСтороны(ShipVisota, float(F.dFreza), F.dMaterial, 0, 0, False, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                ВставитьВырезСОднойСтороны(ShipVisota, float(F.dFreza), F.dMaterial, 2, 0, False, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                ВставитьШипСОднойСтороны(ShipDlina, float(F.dFreza), F.DMaterialDna, 3, 0, F.SmeshenieDno, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
            else:
                pass
                ВставитьВырезСОднойСтороны(ShipVisota, float(F.dFreza), F.dMaterial, 0, F.DMaterialDna, DelatKrishku, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                ВставитьВырезСОднойСтороны(ShipVisota, float(F.dFreza), F.dMaterial, 2, -F.DMaterialDna, DelatKrishku, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                ВставитьВырезСОднойСтороны(ShipDlina, float(F.dFreza), F.DMaterialDna, 3, 0, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
                if DelatKrishku == True:
                    ВставитьВырезСОднойСтороны(ShipDlina, float(F.dFreza), F.DMaterialDna, 1, 0, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
        i = 0
        N = vint(vint(F.KolPeregorodokPoDline))
        Inc_X_Peregorodki = (float(F.dlinna) - 2 * float(F.dMaterial) - vint(F.KolPeregorodokPoDline) * float(F.TolshinaPeregorodok)) / (vint(F.KolPeregorodokPoDline) + 1)
        X_Peregorodki = Inc_X_Peregorodki + F.dMaterial
        if DelatPeregorodki == True:
            while i < N:
                if F.OptionButton1 == True:
                    ВставитьВырезыПодШипыВСередине(float(X_Peregorodki), F.DlinaShipa, float(F.dFreza), F.TolshinaPeregorodok, 0, float(F.DMaterialDna) + float(SmeschDna), F.VisotaPeregorodok)
                if F.OptionButton2 == True:
                    ВставитьВырезыПодШипыВСередине(float(X_Peregorodki), ((float(F.visota) - float(SmeschDna)) / (F.KolPoVisote * 2 + 1)), float(F.dFreza), F.TolshinaPeregorodok, 0, float(F.DMaterialDna) + float(SmeschDna), F.VisotaPeregorodok, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                i = i + 1
                X_Peregorodki = X_Peregorodki + Inc_X_Peregorodki + F.TolshinaPeregorodok
        pass
        DlinaOkr = 0
        DlinaOkr = PI * (float(F.visota) - float(F.DMaterialDna)) / 2
        x1 = Zazor_vokrug_kvadrata * 2 + float(F.visota)
        y1 = ActivePage.SizeHeight / 2 - float(F.shirina) / 2 - SmeschKr
        if DelatProrezi == True:
            x2 = x1 + (float(F.dlinna) + SmeschKr) * 2 + DlinaOkr
            F.ProrRasstOtKraya = (float(F.dlinna) + float(SmeschKr))
            F.RazmerPror = DlinaOkr
        else:
            pass
            x2 = x1 + float(F.dlinna) + SmeschKr
        y2 = ActivePage.SizeHeight / 2 + float(F.shirina) / 2 + SmeschKr
        ActiveLayer.CreateRectangle(x1, y1, x2, y2)
        DnoM2 = DnoM2 + (float(F.shirina) * float(F.dlinna))
        if DelatProrezi == True:
            ВставитьШипСОднойСтороны(ShipShirina, float(F.dFreza), F.dMaterial, 0, float(SmeschKr), float(SmeschKr), True, count=int(F.KolPoShirine) if F.OptionButton2 else None)
            ВставитьШипСОднойСтороны(ShipDlina, float(F.dFreza), F.dMaterial, 1, -float((float(F.dlinna) + SmeschKr * 2) + DlinaOkr), float(SmeschKr), False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
            ВставитьШипСОднойСтороны(ShipDlina, float(F.dFreza), F.dMaterial, 3, float((float(F.dlinna) + SmeschKr * 2) + DlinaOkr), float(SmeschKr), False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
            РисуемПрорези(0)
        else:
            pass
            if DnoVPaz == True:
                ВставитьВырезСОднойСтороны(ShipShirina, float(F.dFreza), F.dMaterial, 0, 0, False, count=int(F.KolPoShirine) if F.OptionButton2 else None)
                ВставитьВырезСОднойСтороны(ShipDlina, float(F.dFreza), F.dMaterial, 1, 0, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
                ВставитьВырезСОднойСтороны(ShipShirina, float(F.dFreza), F.dMaterial, 2, 0, False, count=int(F.KolPoShirine) if F.OptionButton2 else None)
                ВставитьВырезСОднойСтороны(ShipDlina, float(F.dFreza), F.dMaterial, 3, 0, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
            else:
                pass
                ВставитьШипСОднойСтороны(ShipShirina, float(F.dFreza), F.dMaterial, 0, 0, 0, False, count=int(F.KolPoShirine) if F.OptionButton2 else None)
                ВставитьШипСОднойСтороны(ShipDlina, float(F.dFreza), F.dMaterial, 1, 0, 0, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
                ВставитьШипСОднойСтороны(ShipShirina, float(F.dFreza), F.dMaterial, 2, 0, 0, False, count=int(F.KolPoShirine) if F.OptionButton2 else None)
                ВставитьШипСОднойСтороны(ShipDlina, float(F.dFreza), F.dMaterial, 3, 0, 0, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
        i = 0
        N = vint(vint(F.KolPeregorodokPoDline))
        Inc_X_Peregorodki = (float(F.dlinna) - 2 * float(F.dMaterial) - vint(F.KolPeregorodokPoDline) * float(F.TolshinaPeregorodok)) / (vint(F.KolPeregorodokPoDline) + 1)
        X_Peregorodki = Inc_X_Peregorodki + float(F.dMaterial)
        if DelatPeregorodki == True:
            while i < N:
                ВставитьВырезыПодШипыВСередине(float(X_Peregorodki), ShipShirina, float(F.dFreza), float(F.TolshinaPeregorodok), 0, 0, float(F.shirina), count=int(F.KolPoShirine) if F.OptionButton2 else None)
                i = i + 1
                X_Peregorodki = X_Peregorodki + Inc_X_Peregorodki + float(F.TolshinaPeregorodok)
        ActiveDocument.SelectionRange.Shapes.First.Name = "DNO"
        pass
        x1 = Zazor_vokrug_kvadrata * 2 + float(F.visota)
        y1 = Zazor_vokrug_kvadrata
        if DelatProrezi == True:
            x1 = x1 + F.visota / 2
            y1 = y1 - Zazor_vokrug_kvadrata
        x2 = x1 + float(F.dlinna)
        y2 = y1 + float(F.visota)
        ActiveLayer.CreateRectangle(x1, y1, x2, y2)
        MaterialM2 = MaterialM2 + (float(F.dlinna) * float(F.visota))
        if DelatProrezi == True:
            ВставитьВырезСОднойСтороны(ShipVisota, float(F.dFreza), F.dMaterial, 0, -F.DMaterialDna, DelatKrishku, count=int(F.KolPoVisote) if F.OptionButton2 else None)
            ВставитьВырезСОднойСтороны(ShipDlina, float(F.dFreza), F.DMaterialDna, 1, 0, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
            РисуемДугу(2, 2)
            Inc_X_Peregorodki = float(F.dlinna) - 2 * float(F.dMaterial)
            X_Peregorodki = Inc_X_Peregorodki + F.dMaterial
            ВставитьВырезыПодШипыВСередине(float(X_Peregorodki), ((float(F.visota) - float(SmeschDna)) / (F.KolPoVisote * 2 + 1)), float(F.dFreza), F.dMaterial, 0, -float(F.DMaterialDna) - float(SmeschDna), F.VisotaPeregorodok, count=int(F.KolPoVisote) if F.OptionButton2 else None)
        else:
            pass
            if DnoVPaz == True:
                ВставитьВырезСОднойСтороны(ShipVisota, float(F.dFreza), F.dMaterial, 0, 0, False, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                ВставитьШипСОднойСтороны(ShipDlina, float(F.dFreza), F.DMaterialDna, 1, 0, float(SmeschDna), False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
                ВставитьВырезСОднойСтороны(ShipVisota, float(F.dFreza), F.dMaterial, 2, 0, False, count=int(F.KolPoVisote) if F.OptionButton2 else None)
            else:
                pass
                ВставитьВырезСОднойСтороны(ShipVisota, float(F.dFreza), F.dMaterial, 0, -F.DMaterialDna, DelatKrishku, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                ВставитьВырезСОднойСтороны(ShipDlina, float(F.dFreza), F.DMaterialDna, 1, 0, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
                ВставитьВырезСОднойСтороны(ShipVisota, float(F.dFreza), F.dMaterial, 2, F.DMaterialDna, DelatKrishku, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                if DelatKrishku == True:
                    ВставитьВырезСОднойСтороны(ShipDlina, float(F.dFreza), F.DMaterialDna, 3, 0, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
        i = 0
        N = vint(vint(F.KolPeregorodokPoDline))
        Inc_X_Peregorodki = (float(F.dlinna) - 2 * float(F.dMaterial) - vint(F.KolPeregorodokPoDline) * float(F.TolshinaPeregorodok)) / (vint(F.KolPeregorodokPoDline) + 1)
        X_Peregorodki = Inc_X_Peregorodki + F.dMaterial
        if DelatPeregorodki == True:
            while i < N:
                if F.OptionButton1 == True:
                    ВставитьВырезыПодШипыВСередине(float(X_Peregorodki), F.DlinaShipa, float(F.dFreza), F.TolshinaPeregorodok, 2, float(F.DMaterialDna) + float(SmeschDna), F.VisotaPeregorodok)
                if F.OptionButton2 == True:
                    ВставитьВырезыПодШипыВСередине(float(X_Peregorodki), ((float(F.visota) - float(SmeschDna)) / (F.KolPoVisote * 2 + 1)), float(F.dFreza), F.TolshinaPeregorodok, 2, float(F.DMaterialDna) + float(SmeschDna), F.VisotaPeregorodok, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                i = i + 1
                X_Peregorodki = X_Peregorodki + Inc_X_Peregorodki + F.TolshinaPeregorodok
        pass
        if DelatProrezi == False:
            x1 = Zazor_vokrug_kvadrata * 3 + float(F.visota) + float(F.dlinna)
            y1 = ActivePage.SizeHeight / 2 - float(F.shirina) / 2
            x2 = x1 + float(F.visota)
            y2 = y1 + float(F.shirina)
        else:
            pass
            x1 = Zazor_vokrug_kvadrata * 5 + float(F.visota) + float(F.dlinna) * 2 + DlinaOkr
            y1 = ActivePage.SizeHeight / 2 - float(F.shirina) / 2
            x2 = x1 + float(F.visota) - float(F.DMaterialDna) - SmeschDna
            y2 = y1 + float(F.shirina)
        ActiveLayer.CreateRectangle(x1, y1, x2, y2)
        MaterialM2 = MaterialM2 + (float(F.shirina) * float(F.visota))
        if DelatProrezi == True:
            ВставитьВырезСОднойСтороны(((float(F.visota) - float(SmeschDna)) / (F.KolPoVisote * 2 + 1)), float(F.dFreza), F.dMaterial, 1, 0, False, count=int(F.KolPoVisote) if F.OptionButton2 else None)
            ВставитьВырезСОднойСтороны(((float(F.visota) - float(SmeschDna)) / (F.KolPoVisote * 2 + 1)), float(F.dFreza), F.dMaterial, 3, 0, False, count=int(F.KolPoVisote) if F.OptionButton2 else None)
        else:
            pass
            if DnoVPaz == True:
                ВставитьШипСОднойСтороны(ShipShirina, float(F.dFreza), F.DMaterialDna, 0, 0, F.SmeshenieDno, False, count=int(F.KolPoShirine) if F.OptionButton2 else None)
                ВставитьШипСОднойСтороны(ShipVisota, float(F.dFreza), F.dMaterial, 1, 0, 0, False, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                ВставитьШипСОднойСтороны(ShipVisota, float(F.dFreza), F.dMaterial, 3, 0, 0, False, count=int(F.KolPoVisote) if F.OptionButton2 else None)
            else:
                pass
                ВставитьВырезСОднойСтороны(ShipShirina, float(F.dFreza), F.DMaterialDna, 0, 0, False, count=int(F.KolPoShirine) if F.OptionButton2 else None)
                ВставитьШипСОднойСтороны(ShipVisota, float(F.dFreza), F.dMaterial, 1, F.DMaterialDna, 0, DelatKrishku, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                ВставитьШипСОднойСтороны(ShipVisota, float(F.dFreza), F.dMaterial, 3, -F.DMaterialDna, 0, DelatKrishku, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                if DelatKrishku == True:
                    ВставитьВырезСОднойСтороны(ShipShirina, float(F.dFreza), F.DMaterialDna, 2, 0, False, count=int(F.KolPoShirine) if F.OptionButton2 else None)
        i = 0
        N = vint(vint(F.KolPeregorodokPoShirine))
        Inc_X_Peregorodki = (float(F.shirina) - 2 * float(F.dMaterial) - vint(F.KolPeregorodokPoShirine) * float(F.TolshinaPeregorodok)) / (vint(F.KolPeregorodokPoShirine) + 1)
        X_Peregorodki = Inc_X_Peregorodki + F.dMaterial
        if DelatPeregorodki == True:
            while i < N:
                if F.OptionButton1 == True:
                    ВставитьВырезыПодШипыВСередине(float(X_Peregorodki), F.DlinaShipa, float(F.dFreza), F.TolshinaPeregorodok, 1, float(F.DMaterialDna) + float(SmeschDna), F.VisotaPeregorodok)
                if F.OptionButton2 == True:
                    ВставитьВырезыПодШипыВСередине(float(X_Peregorodki), (((float(F.visota) - float(SmeschDna)) - float(F.DMaterialDna)) / (F.KolPoVisote * 2 + 1)), float(F.dFreza), F.TolshinaPeregorodok, 1, float(F.DMaterialDna) + float(SmeschDna), F.VisotaPeregorodok, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                i = i + 1
                X_Peregorodki = X_Peregorodki + Inc_X_Peregorodki + F.TolshinaPeregorodok
        pass
        if DelatPeregorodki == True:
            x1 = Zazor_vokrug_kvadrata * 4 + 2 * float(F.visota) + float(F.dlinna)
            y1 = ActivePage.SizeHeight / 2 - float(F.shirina) / 2
            x2 = x1 + float(F.VisotaPeregorodok) - SmeschDna
            y2 = y1 + float(F.shirina)
            i = 0
            N = vint(vint(F.KolPeregorodokPoDline))
            while i < N:
                ActiveLayer.CreateRectangle(x1, y1, x2, y2)
                PeregorodkaM2 = PeregorodkaM2 + ((y2 - y1) * (x2 - x1))
                if F.OptionButton1 == True:
                    ВставитьВырезСОднойСтороны(ShipDlina, float(F.dFreza), F.DMaterialDna, 0, 0, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
                    ВставитьВырезСОднойСтороны(ShipDlina, float(F.dFreza), F.dMaterial, 1, F.DMaterialDna, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
                    ВставитьВырезСОднойСтороны(ShipDlina, float(F.dFreza), F.dMaterial, 3, -F.DMaterialDna, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
                    if floor(F.KolPeregorodokPoShirine) > 0:
                        ВставитьВырезПерегородкиСОднойСтороны(floor(F.KolPeregorodokPoShirine), float(F.TolshinaPeregorodok), float(F.dFreza), float(F.dMaterial), float(F.DMaterialDna), 0, 0)
                if F.OptionButton2 == True:
                    ВставитьВырезСОднойСтороны(ShipShirina, float(F.dFreza), F.DMaterialDna, 0, 0, False, count=int(F.KolPoShirine) if F.OptionButton2 else None)
                    ВставитьВырезСОднойСтороны(((float(F.visota) - float(SmeschDna)) / (floor(F.KolPoVisote) * 2 + 1)), float(F.dFreza), F.dMaterial, 1, F.DMaterialDna, False, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                    ВставитьВырезСОднойСтороны(((float(F.visota) - float(SmeschDna)) / (floor(F.KolPoVisote) * 2 + 1)), float(F.dFreza), F.dMaterial, 3, -F.DMaterialDna, False, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                    if floor(F.KolPeregorodokPoShirine) > 0:
                        ВставитьВырезПерегородкиСОднойСтороны(floor(F.KolPeregorodokPoShirine), float(F.TolshinaPeregorodok), float(F.dFreza), float(F.dMaterial), float(F.DMaterialDna), 0, 0)
                i = i + 1
                x1 = x1 + float(F.VisotaPeregorodok) + Zazor_vokrug_kvadrata
                x2 = x2 + float(F.VisotaPeregorodok) + Zazor_vokrug_kvadrata
                ActiveDocument.SelectionRange.Shapes.First.Name = "Peregorodka"
                pass
            if floor(F.KolPeregorodokPoShirine) > 0:
                x1 = Zazor_vokrug_kvadrata * (4 + floor(F.KolPeregorodokPoDline)) + 2 * float(F.visota) + float(F.dlinna) + floor(F.KolPeregorodokPoDline) * float(F.visota)
                y1 = ActivePage.SizeHeight / 2 - float(F.dlinna) / 2
                x2 = x1 + float(F.VisotaPeregorodok) - float(F.DMaterialDna) - float(SmeschDna)
                y2 = y1 + float(F.dlinna)
                i = 0
                N = vint(vint(F.KolPeregorodokPoShirine))
                while i < N:
                    ActiveLayer.CreateRectangle(x1, y1, x2, y2)
                    PeregorodkaM2 = PeregorodkaM2 + ((y2 - y1) * (x2 - x1))
                    if F.OptionButton1 == True:
                        ВставитьВырезСОднойСтороны(ShipDlina, float(F.dFreza), F.dMaterial, 1, 0, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
                        ВставитьВырезСОднойСтороны(ShipDlina, float(F.dFreza), F.dMaterial, 3, 0, False, count=int(F.KolPoDlinne) if F.OptionButton2 else None)
                        if floor(F.KolPeregorodokPoDline) > 0:
                            ВставитьВырезПерегородкиСОднойСтороны(floor(F.KolPeregorodokPoDline), float(F.TolshinaPeregorodok), float(F.dFreza), float(F.dMaterial), 0, 0, 0)
                    if F.OptionButton2 == True:
                        ВставитьВырезСОднойСтороны((((float(F.visota) - float(SmeschDna)) - float(F.DMaterialDna)) / (floor(F.KolPoVisote) * 2 + 1)), float(F.dFreza), F.dMaterial, 1, 0, False, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                        ВставитьВырезСОднойСтороны((((float(F.visota) - float(SmeschDna)) - float(F.DMaterialDna)) / (floor(F.KolPoVisote) * 2 + 1)), float(F.dFreza), F.dMaterial, 3, 0, False, count=int(F.KolPoVisote) if F.OptionButton2 else None)
                        if floor(F.KolPeregorodokPoDline) > 0:
                            ВставитьВырезПерегородкиСОднойСтороны(floor(F.KolPeregorodokPoDline), float(F.TolshinaPeregorodok), float(F.dFreza), float(F.dMaterial), 0, 0, 0)
                    i = i + 1
                    x1 = x1 + float(F.VisotaPeregorodok) - float(F.DMaterialDna) + Zazor_vokrug_kvadrata
                    x2 = x2 + float(F.VisotaPeregorodok) - float(F.DMaterialDna) + Zazor_vokrug_kvadrata
                    ActiveDocument.SelectionRange.Shapes.First.Name = "Peregorodka"
                    pass
        pass
        pass
        pass
        pass
        pass
        pass
        pass
        pass
        pass
        pass
        if F.dMaterial == F.DMaterialDna:
            MaterialM2 = MaterialM2 + DnoM2
            DnoM2 = 0
            if F.dMaterial == F.TolshinaPeregorodok:
                MaterialM2 = MaterialM2 + PeregorodkaM2
                PeregorodkaM2 = 0
            else:
                pass
        else:
            pass
            if F.DMaterialDna == F.TolshinaPeregorodok:
                DnoM2 = DnoM2 + PeregorodkaM2
                PeregorodkaM2 = 0
            else:
                pass
        pass
        pass
        if DnoM2 > 0:
            pass
            pass
        if PeregorodkaM2 > 0:
            pass
            pass
    else:
        pass
        CommandButton5_Click()
    pass
    pass

def CommandButton5_Click():
    global DelatKrishku, DelatProrezi, DelatPeregorodki, DnoVPaz, Zazor_vokrug_kvadrata
    ShipVisota = 0
    ShipDlina = 0
    ShipShirina = 0
    x1 = 0
    x2 = 0
    y1 = 0
    y2 = 0
    MaterialM2 = 0
    DnoM2 = 0
    PeregorodkaM2 = 0
    Zazor_vokrug_kvadrata = 10
    if Application.Documents.Count == 0:
        pass
    pass
    F.shirina = ЗаменаТчкНаЗапт(F.shirina)
    F.visota = ЗаменаТчкНаЗапт(F.visota)
    F.dlinna = ЗаменаТчкНаЗапт(F.dlinna)
    ActivePage.SizeHeight = float(F.shirina) + float(F.visota) * 2 + Zazor_vokrug_kvadrata * 4
    ActivePage.SizeWidth = float(F.dlinna) + float(F.visota) * 2 + float(F.visota) * (vint(F.KolPeregorodokPoDline) + vint(F.KolPeregorodokPoShirine)) + Zazor_vokrug_kvadrata * 4 + Zazor_vokrug_kvadrata * (vint(F.KolPeregorodokPoDline) + vint(F.KolPeregorodokPoShirine))
    x1 = Zazor_vokrug_kvadrata * 2 + float(F.visota)
    y1 = ActivePage.SizeHeight / 2 - float(F.shirina) / 2
    x2 = float(F.visota) + Zazor_vokrug_kvadrata * 2 + float(F.dlinna)
    y2 = ActivePage.SizeHeight / 2 + float(F.shirina) / 2
    ActiveLayer.CreateRectangle(x1, y1, x2, y2)
    DnoM2 = DnoM2 + (float(F.shirina) * float(F.dlinna))
    РисуемПрорези(0)

