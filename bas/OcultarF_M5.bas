Attribute VB_Name = "OcultarF_M5"
Sub OcultarFilaM5()
Application.ScreenUpdating = False
    
    For i = 13 To 62
       
       If Range("B" & i) = "" Then
            Range("B" & i).EntireRow.Hidden = True
        Else
            Range("B" & i).EntireRow.Hidden = False
       End If
       
    Next i
    Sheets("I5").Select
    For i = 13 To 62
       
       If Range("B" & i) = "" Then
            Range("B" & i).EntireRow.Hidden = True
        Else
            Range("B" & i).EntireRow.Hidden = False
       End If
       
    Next i
    Sheets("R5").Select
    For i = 11 To 60
       
       If Range("B" & i) = "" Then
            Range("B" & i).EntireRow.Hidden = True
        Else
            Range("B" & i).EntireRow.Hidden = False
       End If
       
    Next i
    For i = 129 To 178
       
       If Range("B" & i) = "" Then
            Range("B" & i).EntireRow.Hidden = True
        Else
            Range("B" & i).EntireRow.Hidden = False
       End If
       
    Next i
    For i = 247 To 296
       
       If Range("B" & i) = "" Then
            Range("B" & i).EntireRow.Hidden = True
        Else
            Range("B" & i).EntireRow.Hidden = False
       End If
       
    Next i
    For i = 365 To 414
       
       If Range("B" & i) = "" Then
            Range("B" & i).EntireRow.Hidden = True
        Else
            Range("B" & i).EntireRow.Hidden = False
       End If
       
    Next i
    
    For i = 471 To 520
       
       If Range("B" & i) = "" Then
            Range("B" & i).EntireRow.Hidden = True
        Else
            Range("B" & i).EntireRow.Hidden = False
       End If
       
    Next i
    
    Sheets("M5").Select
    Range("B13").Select
    Application.ScreenUpdating = True
    MsgBox "Proceso terminado exitosamente!"

End Sub

