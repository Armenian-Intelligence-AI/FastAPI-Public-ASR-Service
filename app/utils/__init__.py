import utils

def handle_label_greeting(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = f"բարև ձեզ հարգելի Ստուգում"
    if len(labels) == 1:
        message += ", Ի՞նչպես կարող եմ օգնել"
    return utils.format_return_label_data(message)
    
def handle_label_unlabeled(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = f"Կարո՞ղ եք հստակեցնել ձեր հարցը"
    return utils.format_return_label_data(message)
    
def handle_label_personal_info(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = ""
    return utils.format_return_label_data(message)

def handle_label_loan_status(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = "Ահա ձեր վարկերի մանրամասները:\n\n"
    query = f"SELECT * FROM MLfnLoanStatus({event_data.get('customer_id')}, default)"
    result = utils.execute_query_on_db(query)

    for loan in result:
        message += f"Պայմանագրի համարը: {loan['Num']}\n"
        message += f"Մայր գումար: {loan['BaseBalance']}\n"
        message += f"Ընդհանուր մնացորդ: {loan['TotalDebt']}\n"
        message += f"Տույժ տուգանք։: {loan['Fines']}\n"
        message += f"ժամկետանց մնացորդ: {loan['SumOverdueBalance']}\n"
        # Handle PledgeSaleStatus
        pledge_sale_status = loan.get('PledgeSaleStatus')
        if pledge_sale_status:
            if pledge_sale_status == 'NO':
                message += "Վաճառվել է: Ոչ\n"
            elif pledge_sale_status == 'YES':
                message += "Վաճառվել է: Այո\n"
            elif pledge_sale_status == 'Partly':
                message += "Վաճառվել է: Մասամբ\n"
        
        # Handle ConfiscationStatus
        confiscation_status = loan.get('ConfiscationStatus')
        if confiscation_status:
            if confiscation_status == 'NO':
                message += "Բռնագանձված է: Ոչ\n"
            elif confiscation_status == 'YES':
                message += "Բռնագանձված է: Այո\n"

        message += f"Հերթական վճարման ամսաթիվ: {loan['NextPayDate']}\n"
    if not result:
        message: str = "Այս պահին դուք չունեք ակտիվ պայմանագիր\n"
    message += "Բռնագանձման ծանուցումը պարտապանին հանձնելուց երկու ամիս հետո գրավառուն իրավունք ունի ՀՀ օրենսդրությամբ սահմանված կարգով գրավատուի անունից իրացնելու գրավի առարկան ուղղակի վաճառքի կամ հրապարակային սակարկությունների միջոցով: "
    return utils.format_return_label_data(message)

def handle_label_order(event_data: dict, labels: list, self_label: int) -> dict:
    buttons = {
        'order_item': {
            'order_item_id': [
                {"display_name": "0.4գ ոսկի", "return_value": 1},
                {"display_name": "0.1գ ոսկի", "return_value": 2},
                {"display_name": "0.2գ ոսկի", "return_value": 3}
            ],
            'order_branch_id': [
                {"display_name": "24, 48 Tumanyan St, Yerevan", "return_value": 1},
                {"display_name": "1, 4 Marshal Baghramyan Ave, Yerevan", "return_value": 2}
            ]
        },
        'order_get_info': {
            'display_order_information': [
                {"display_name": "Ստանալ տեղեկություն", "return_value": 1}
            ],
        }
    }
    return utils.format_return_label_data("Ի՞նչ կցանկանաք անել՝ պատվիրել ապրանք կամ ստանալ տեղեկություն, թե ինչպես է աշխատում պատվերը։ Ահա տարբերակները", buttons)

def handle_label_ask_to_contact(event_data: dict, labels: list, self_label: int) -> dict:
    utils.send_request_to_call_center(1, None)
    message: str = "մենք ուղարկել ենք ձեր հետ կապ հաստատելու հայտը։ Խնդրում ենք սպասել"
    return utils.format_return_label_data(message)

def handle_label_pledge_question(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = "gրավի մասին տեղեկություն ստանալու համար կարող եք ծանոթանալ մեր կայքում՝ https://www.fastbank.am/ոսկու-գրավով-վարկեր ։ Սեղմելով ներքևում գտնվող կոճակը, մեր աջակցման խումբը կկապնվի ձեզ հետ։"
    buttons = {
        'contact_me': {
            'label': [
                {"display_name": "Կապնվեք ինձ հետ (Գրավ)", "return_value": self_label}
            ],
        }
    }
    return utils.format_return_label_data(message, buttons)

def handle_label_payment_question(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = "Վճարումների մասին տեղեկություն ստանալու համար կարող եք այցելել կայք` https://www.fastbank.am/հաշիվներ-և-փոխանցումներ ։ Սեղմելով ներքևում գտնվող կոճակը, մեր աջակցման խումբը կկապնվի ձեզ հետ։"
    buttons = {
        'contact_me': {
            'label': [
                {"display_name": "Կապնվեքվեք ինձ հետ (Վճարում)", "return_value": self_label}
            ],
        }
    }
    return utils.format_return_label_data(message, buttons)

def handle_label_contract_number(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = "Ահա ձեր պայմանագրերի մանրամասները:\n\n"
    query = f"SELECT * FROM MLfnContractNumber({event_data.get('customer_id')}, default)"
    result = utils.execute_query_on_db(query)
    print(result)
    for contract in result:
        if 'Num' in contract:
            message += f"Պայմանագրի համարը: {contract['Num']}\n"
            message += f"Կնքման ամսաթիվ: {contract.get('Date', 'Տվյալները բացակայում են')}\n"
            message += f"Ավարտի ամսաթիվ: {contract.get('MatDate', 'Տվյալները բացակայում են')}\n"
            message += f"Ընդհանուր մնացորդ: {contract.get('TotalSum', 'Տվյալները բացակայում են')}\n\n"
            message += f"Տույժ տուգանք։: {contract.get('Fines', 'Տվյալները բացակայում են')}\n"
    if not result:
        message: str = "Այս պահին դուք չունեք ակտիվ պայմանագիր"
    return utils.format_return_label_data(message)

def handle_label_branch_question(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = "Մասնաճյուղերի մասին տեղեկատվություն ստանալու համար այցելեք մեր կայք` https://www.fastbank.am/մասնաճյուղեր "
    return utils.format_return_label_data(message)
    
def handle_label_gold_price(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = (
        "ներկայիս ոսկու գինը կարող եք տեսնել հետևյալ հղումով՝ "
        "https://www.fastbank.am/ոսկու-գրավով-վարկեր \n\n"
        "Խնդրում ենք այցելել մեր կայքը, որպեսզի ստանաք թարմացված տվյալներ"
    )
    return utils.format_return_label_data(message)

def handle_label_thanks(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = "Եթե ունեք այլ հարցեր կամ օգնության կարիք, խնդրում ենք տեղեկացնել"
    return utils.format_return_label_data(message)

def handle_label_delay_question(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = ""
    return utils.format_return_label_data(message)

def handle_label_payment_size(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = "ահա ձեր ամսական վճարումների մանրամասները:\n\n"
    query = f"SELECT * FROM MLfnPaymentSize({event_data.get('customer_id')}, default)"
    result = utils.execute_query_on_db(query)
    for payment in result:
        message += f"Պայմանագրի համարը: {payment['Num']}\n"
        message += f"Վճարման ամսաթիվ: {payment['PayDate']}\n"
        message += f"Հերթական մարում: {payment.get('CurrentTotalAmount', 'Տվյալները բացակայում են')}\n\n"
        message += f"Վճարման ենթակա տոկոսագումար: {payment.get('IntAmount', 'Տվյալները բացակայում են')}\n"
        message += f"Վճարման ենթակա վարձավճար: {payment.get('FeeAmount', 'Տվյալները բացակայում են')}\n"
        message += f"Ընդհանուր մնացորդ: {payment.get('TotalDebt', 'Տվյալները բացակայում են')}\n"

    if not result:
        message: str = "Այս պահին դուք չունեք ակտիվ պայմանագիր"
    message += (
        "Լրացուցիչ տեղեկությունների համար այցելեք մեր կայքը՝ "
        "https://www.fastbank.am "
    )
    return utils.format_return_label_data(message)

def handle_label_loan_question(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = (
        "Վարկերի վերաբերյալ մանրամասներ ստանալու համար այցելեք՝ "
        "https://www.fastbank.am/բիզնեսի-վարկեր \n\n"
        "Վարկի խորհրդատվության հայտի համար այցելեք՝ "
        "https://www.fastbank.am/բիզնես-վարկային-հայտ "
    )
    return utils.format_return_label_data(message)

def handle_label_payment_date(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = "Ահա ձեր վճարումների ամսաթվերը:\n\n"
    
    query = f"SELECT * FROM MLfnPaymentSize({event_data.get('customer_id')}, default)"
    result = utils.execute_query_on_db(query)
    for payment in result:
        message += f"Պայմանագրի համարը: {payment['Num']}\n"
        message += f"Վճարման ամսաթիվ: {payment['PayDate']}\n"
        message += f"Հերթական մարում: {payment.get('CurrentTotalAmount', 'Տվյալները բացակայում են')}\n"
        message += f"Վճարման ենթակա տոկոսագումար: {payment.get('IntAmount', 'Տվյալները բացակայում են')}\n"
        message += f"Վճարման ենթակա վարձավճար: {payment.get('FeeAmount', 'Տվյալները բացակայում են')}\n"
        message += f"Ընդհանուր մնացորդ: {payment.get('TotalDebt', 'Տվյալները բացակայում են')}\n\n"

    if not result:
        message: str = "Այս պահին դուք չունեք ակտիվ պայմանագիր"
    message += (
        "Լրացուցիչ տեղեկությունների համար այցելեք մեր կայքը՝ "
        "https://www.fastbank.am "
    )
    return utils.format_return_label_data(message)


def handle_label_reloaning(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = ""
    return utils.format_return_label_data(message)

def handle_label_payment_status(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = "ահա ձեր վերջին 10 վճարումները:\n\n"
    
    query = f"SELECT * FROM MLfnPaymentStatus({event_data.get('customer_id')}, default)"
    result = utils.execute_query_on_db(query)
    for payment in result:
        message += f"Վճարման համարը: {payment['Num']}\n"
        message += f"Արժույթ: {payment['CurrencyId']}\n"
        message += f"Վճարման ամսաթիվ: {payment['TranDate']}\n"
        message += f"Վճարման տեսակը: {payment['TranKindName']}\n"
        message += f"Վճարման գումարը: {payment['Amount']} {payment['CurrencyId']}\n\n"
        
    if not result:
        message: str = "Այս պահին դուք չունեք ակտիվ պայմանագիր"
    message += (
        "Լրացուցիչ տեղեկությունների համար այցելեք մեր կայքը՝ "
        "https://www.fastbank.am "
    )
    return utils.format_return_label_data(message)

def handle_label_order_status(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = "Ահա ձեր պատվերների կարգավիճակը:\n\n"
    
    # Dummy order status data
    orders = [
        {"պատվերի համարը": "ORD123456", "վիճակ": "Մշակման փուլում", "մատակարարման ամսաթիվ": "01-07-2024"},
        {"պատվերի համարը": "ORD789012", "վիճակ": "Հասցվել է", "մատակարարման ամսաթիվ": "20-06-2024"},
        {"պատվերի համարը": "ORD345678", "վիճակ": "Չեղարկված", "մատակարարման ամսաթիվ": "N/A"},
    ]
    
    for order in orders:
        message += f"Պատվերի համարը: {order['պատվերի համարը']}\n"
        message += f"Վիճակ: {order['վիճակ']}\n"
        message += f"Մատակարարման ամսաթիվ: {order['մատակարարման ամսաթիվ']}\n\n"

    return utils.format_return_label_data(message)

def handle_label_arrive(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = (
        "մեր մասնաճյուղերի մասին տեղեկանալու և այցելելու համար այցելեք՝ "
        "https://www.fastbank.am/մասնաճյուղեր "
    )
    if 9 in labels:
        message: str = ""
    return utils.format_return_label_data(message)
    
def handle_label_help_request(event_data: dict, labels: list, self_label: int) -> dict:
    if len(labels) == 1:
        message: str = "Ինչպե՞ս կարող եմ օգնել ձեզ"
    elif len(labels) == 2 and 7 in labels:
        message: str = "Ինչպե՞ս կարող եմ օգնել ձեզ"
    else:
        message: str = ""

    return utils.format_return_label_data(message)

def handle_label_ok(event_data: dict, labels: list, self_label: int) -> dict:
    if len(labels) == 1:
        message: str = "Եթե ունեք այլ հարցեր, խնդրում եմ տեղեկացրեք"
    else:
        message: str = ""

    return utils.format_return_label_data(message)

def handle_label_complaint(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = (
        "ձեր բողոքը ներկայացնելու համար Խնդրում ենք մուտք գործել "
        "https://www.fastbank.am/հետադարձ-կապ և լրացնել հայտը "
    )
    return utils.format_return_label_data(message)

def handle_label_ask_to_save(event_data: dict, labels: list, self_label: int) -> dict:
    utils.send_request_to_call_center(1, self_label)
    message: str = "խնդրում ենք սպասել, գրավի պահպանման հարցով մեր մասնագետը կկապնվի ձեզ հետ"
    return utils.format_return_label_data(message)

def handle_label_vacancy(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = (
        "աշխատանքի հնարավորությունների մասին տեղեկանալու համար այցելեք՝ "
        "https://www.fastbank.am/աշխատանք "
    )
    return utils.format_return_label_data(message)

def handle_label_accreditation(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = ""
    return utils.format_return_label_data(message)

def handle_label_terminal_related(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = (
        "տերմինալների տեղակայման վայրերի կամ կոնտակտային հեռախոսահամարների մասին տեղեկանալու համար այցելեք՝ "
        "https://www.fastshift.am/en/մասնաճյուղեր-տերմինալներ "
    )
    return utils.format_return_label_data(message)

def handle_label_rename(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = ""
    return utils.format_return_label_data(message)

def handle_label_exchange_rate(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = (
        "փոխարժեքների վերաբերյալ տեղեկություններ ստանալու համար այցելեք՝ "
        "https://https://www.fastbank.am/ և միջին մասում կգտնեք փոխարժեքների վերաբերյալ տեղեկատվությունը"
    )
    return utils.format_return_label_data(message)

def handle_label_unable_to_pay(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = "մենք ցավում ենք, որ դուք չեք կարող վճարել: Սեղմելով ներքևում գտնվող կոճակը, մեր աշխատակիցները կկապնվեն ձեզ հետ"
    buttons = {
        'contact_me': {
            'label': [
                {"display_name": "Կապնվեք ինձ հետ (Վճարման խնդիր)", "return_value": self_label}
            ],
        }
    }
    return utils.format_return_label_data(message, buttons)

def handle_label_black_list(event_data: dict, labels: list, self_label: int) -> dict:
    utils.send_request_to_call_center(1, self_label)
    message: str = "սև ցուցակի հարցով մեր մասնագետը կկապնվի ձեզ հետ"
    return utils.format_return_label_data(message)

def handle_label_auction(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = (
        "աճուրդները տեսնելու համար այցելեք՝ "
        "https://fcachurd.am/hy/gold-auction/upcoming# "
    )
    return utils.format_return_label_data(message)

def handle_label_proposal(event_data: dict, labels: list, self_label: int) -> dict:
    utils.call_bank_internal_api({'data': event_data}, 'POST')
    message: str = (
        "Ձեր առաջարկը կուղարկվի մեր մասնագետին: Եթե մեզ հետաքրքրի, մենք կկապվենք ձեզ հետ"
    )
    return utils.format_return_label_data(message)

def handle_label_yes(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = ""
    return utils.format_return_label_data(message)

def handle_label_loan_contract(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = "Ահա ձեր բոլոր վարկային պայմանագրերը:\n\n"
    
    # Dummy loan contract data
    loans = [
        {"պայմանագրի համարը": "LC123456", "գումար": "500000", "ստորագրման ամսաթիվ": "01-01-2023", "վերջնաժամկետ": "01-01-2025"},
        {"պայմանագրի համարը": "LC789012", "գումար": "250000", "ստորագրման ամսաթիվ": "15-03-2023", "վերջնաժամկետ": "15-03-2026"},
        {"պայմանագրի համարը": "LC345678", "գումար": "300000", "ստորագրման ամսաթիվ": "10-06-2022", "վերջնաժամկետ": "10-06-2024"},
        # Add more loan contract data as needed
    ]
    
    for loan in loans:
        message += f"Պայմանագրի համարը: {loan['պայմանագրի համարը']}\n"
        message += f"Գումար: {loan['գումար']}\n"
        message += f"Ստորագրման ամսաթիվ: {loan['ստորագրման ամսաթիվ']}\n"
        message += f"Վերջնաժամկետ: {loan['վերջնաժամկետ']}\n\n"
    
    return utils.format_return_label_data(message)

def handle_label_fast_transactions(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = (
        "արագ փոխանցումների վերաբերյալ մանրամասն տեղեկությունների համար այցելեք՝ "
        "https://www.fastbank.am/հաշիվներ-և-փոխանցումներ "
    )
    return utils.format_return_label_data(message)

def handle_label_deposit_question(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = (
        "ավանդների վերաբերյալ տեղեկություններ ստանալու համար այցելեք՝ "
        "https://www.fastbank.am/ավանդ-ֆիզ-անձ "
    )
    return utils.format_return_label_data(message)

def handle_label_cancel_order(event_data: dict, labels: list, self_label: int) -> dict:
    buttons = {
        'cancel_order_item': {
            'cancel_order_item_id': [
                {"display_name": "0.4գ ոսկի", "return_value": 1},
                {"display_name": "0.1գ ոսկի", "return_value": 2},
                {"display_name": "0.2գ ոսկի", "return_value": 3}
            ]
        }
    }
    return utils.format_return_label_data("ո՞ր պատվերն եք ուզում չեղարկել", buttons)

def handle_label_relinquished_pledge(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = (
        "խնդրում ենք լրացնել հայտ՝ https://www.fastbank.am/հետադարձ-կապ , գրավից հրաժարվելու վերաբերյալ տեղեկություններ ներկայացնելու համար"
    )
    return utils.format_return_label_data(message)

def handle_label_register(event_data: dict, labels: list, self_label: int) -> dict:
    utils.send_request_to_call_center(1, self_label)
    message: str = "Մեր մասնագետը կկապնվի ձեզ հետ գրանցման հարցերի համար։"
    return utils.format_return_label_data(message)

def handle_label_no(event_data: dict, labels: list, self_label: int) -> dict:
    message: str = ""
    return utils.format_return_label_data(message)
