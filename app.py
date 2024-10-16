from flask import Flask, request, jsonify

app = Flask(__name__)

def calculate_poker_transactions(start_blinds, end_blinds):
    assert len(start_blinds) == len(end_blinds), "The number of players must be the same"
    assert sum(start_blinds) == sum(end_blinds), "The total number of blinds must be the same but the sum of start_blinds is {} and the sum of end_blinds is {}".format(sum(start_blinds), sum(end_blinds))
    # Calculate the net gain/loss for each player
    net_blinds = [end - start for start, end in zip(start_blinds, end_blinds)]
    
    # Separate the players into creditors and debtors
    creditors = [(i, net) for i, net in enumerate(net_blinds) if net > 0]
    debtors = [(i, -net) for i, net in enumerate(net_blinds) if net < 0]
    
    transactions = []
    
    # Minimize transactions by matching creditors and debtors
    i, j = 0, 0
    while i < len(creditors) and j < len(debtors):
        creditor_index, credit_amount = creditors[i]
        debtor_index, debt_amount = debtors[j]
        
        # Determine the transaction amount
        transaction_amount = min(credit_amount, debt_amount)
        
        # Record the transaction
        transactions.append((debtor_index, creditor_index, transaction_amount))
        
        # Update the remaining amounts
        creditors[i] = (creditor_index, credit_amount - transaction_amount)
        debtors[j] = (debtor_index, debt_amount - transaction_amount)
        
        # Move to the next creditor or debtor if fully settled
        if creditors[i][1] == 0:
            i += 1
        if debtors[j][1] == 0:
            j += 1
    return transactions

@app.route('/')
def index():
    """ Ask the user for inputs """
    return """
    <form action="/calculate" method="post">
        <label for="start_blinds">Start blinds:</label>
        <input type="text" name="start_blinds" id="start_blinds"><br>
        <label for="end_blinds">End blinds:</label>
        <input type="text" name="end_blinds" id="end_blinds"><br>
        <label for="player_names">Player names (optional, comma-separated):</label>
        <input type="text" name="player_names" id="player_names"><br>
        <label for="big_blind">Big Blind size (optional, in euros):</label>
        <input type="text" name="big_blind" id="big_blind"><br>
        <input type="submit" value="Calculate">
    </form>
    """
    
@app.route('/calculate', methods=['POST'])
def calculate():
    """ Calculate the transactions """
    try:
        start_blinds = [float(x) for x in request.form['start_blinds'].split(',')]
        end_blinds = [float(x) for x in request.form['end_blinds'].split(',')]
        
        # Optional player names
        player_names = request.form.get('player_names', '')
        if player_names:
            player_names = player_names.split(',')
        else:
            player_names = [f'Player{i}' for i in range(len(start_blinds))]
        
        # Optional big blind size
        big_blind = request.form.get('big_blind', '')
        if big_blind:
            big_blind = float(big_blind)
        else:
            big_blind = None
        
        # Verify input lengths
        if len(start_blinds) != len(end_blinds):
            return jsonify({"error": "The number of start blinds and end blinds must be the same"}), 400
        if len(player_names) != len(start_blinds):
            return jsonify({"error": "The number of player names must match the number of blinds"}), 400
        
        transactions = calculate_poker_transactions(start_blinds, end_blinds)
        
        # Format the transactions with player names
        formatted_transactions = []
        for debtor, creditor, amount in transactions:
            transaction = {
                "from": player_names[debtor],
                "to": player_names[creditor],
                "amount_in_blinds": amount
            }
            if big_blind:
                transaction["amount_in_euros"] = amount * big_blind
            formatted_transactions.append(transaction)
        
        return jsonify(formatted_transactions)
    except AssertionError as e:
        return jsonify({"error": str(e)}), 400
    
    