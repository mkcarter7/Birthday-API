"""
Trivia Game ViewSet
Provides trivia questions and validates answers for the Party Trivia game
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..models import GameScore, Party


# Base trivia question templates - will be personalized per party
TRIVIA_QUESTION_TEMPLATES = [
    {
        "id": 1,
        "category": "Personal",
        "template": "What is the birthday {gender}'s favorite color?",
        "options_template": None,  # Will be set dynamically based on party
        "correct_answer": 0,
        "points": 20
    },
    {
        "id": 2,
        "category": "Personal",
        "template": "What is the birthday {gender}'s favorite animal?",
        "options_template": None,
        "correct_answer": 0,
        "points": 20
    },
    {
        "id": 3,
        "category": "Personal",
        "template": "Where was the birthday {gender} born?",
        "options_template": None,
        "correct_answer": 0,
        "points": 25
    },
    {
        "id": 4,
        "category": "Personal",
        "template": "What color are the birthday {gender}'s eyes?",
        "options_template": None,
        "correct_answer": 0,
        "points": 15
    },
    {
        "id": 5,
        "category": "Personal",
        "template": "What size shoe does the birthday {gender} wear?",
        "options_template": None,
        "correct_answer": 0,
        "points": 20
    },
    {
        "id": 6,
        "category": "Personal",
        "template": "What is the birthday {gender}'s favorite song?",
        "options_template": None,
        "correct_answer": 0,
        "points": 20
    },
]


def get_personalized_questions(party):
    """
    Generate personalized trivia questions for a specific party
    Uses mock data for now - in production, these would come from party settings or party host profile
    """
    host_name = party.host.first_name or party.host.username
    # Determine gender from name or default to "girl/boy"
    gender = "girl"  # Default - can be customized per party
    
    # Mock answers - in production these would be stored in Party model or separate TriviaAnswers model
    mock_answers = {
        1: {  # Favorite color
            "options": ["Blue", "Red", "Purple", "Green"],
            "correct": 0  # Blue
        },
        2: {  # Favorite animal
            "options": ["Dog", "Cat", "Elephant", "Dolphin"],
            "correct": 1  # Cat
        },
        3: {  # Birth place
            "options": ["New York", "Los Angeles", "Chicago", "Miami"],
            "correct": 0  # New York
        },
        4: {  # Eye color
            "options": ["Brown", "Blue", "Green", "Hazel"],
            "correct": 1  # Blue
        },
        5: {  # Shoe size
            "options": ["Size 7", "Size 8", "Size 9", "Size 10"],
            "correct": 2  # Size 9
        },
        6: {  # Favorite song
            "options": ["Song A", "Song B", "Song C", "Song D"],
            "correct": 0  # Song A
        },
    }
    
    questions = []
    for template in TRIVIA_QUESTION_TEMPLATES:
        question_data = mock_answers.get(template["id"], {
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "correct": 0
        })
        
        questions.append({
            "id": template["id"],
            "category": template["category"],
            "question": template["template"].format(gender=gender),
            "options": question_data["options"],
            "correct_answer": question_data["correct"],
            "points": template["points"]
        })
    
    return questions


class TriviaViewSet(viewsets.ViewSet):
    """
    ViewSet for Trivia Game
    Provides endpoints for getting trivia questions and submitting answers
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def questions(self, request):
        """
        Get personalized trivia questions for a party about the birthday person
        Query params:
        - party: Party ID (required)
        - count: Number of questions (default: 6, max: 6)
        """
        party_id = request.query_params.get('party')
        if not party_id:
            return Response(
                {'error': 'Party ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify party exists
        try:
            party = Party.objects.get(pk=party_id)
        except Party.DoesNotExist:
            return Response(
                {'error': 'Party not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get personalized questions for this party
        questions = get_personalized_questions(party)
        
        # Get question count (default 6, max 6 since we have 6 questions)
        count = min(int(request.query_params.get('count', 6)), len(questions))
        
        # Select questions (take first N)
        selected_questions = questions[:count]
        
        # Remove correct_answer from response (only show options)
        questions_for_frontend = []
        for q in selected_questions:
            questions_for_frontend.append({
                'id': q['id'],
                'category': q['category'],
                'question': q['question'],
                'options': q['options'],
                'points': q['points']
            })
        
        return Response({
            'party': {
                'id': party.id,
                'name': party.name
            },
            'questions': questions_for_frontend,
            'total_questions': len(questions_for_frontend)
        })
    
    @action(detail=False, methods=['post'])
    def submit(self, request):
        """
        Submit trivia game answers and award points
        Expected payload:
        {
            "party": 1,
            "answers": [
                {"question_id": 1, "answer": 0},
                {"question_id": 2, "answer": 0}
            ]
        }
        """
        party_id = request.data.get('party')
        answers = request.data.get('answers', [])
        
        if not party_id:
            return Response(
                {'error': 'Party ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not answers or not isinstance(answers, list):
            return Response(
                {'error': 'Answers array is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify party exists
        try:
            party = Party.objects.get(pk=party_id)
        except Party.DoesNotExist:
            return Response(
                {'error': 'Party not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get or create game score for this user/party
        score, created = GameScore.objects.get_or_create(
            user=request.user,
            party=party,
            defaults={'total_points': 0, 'level': 1}
        )
        
        # Get personalized questions for this party to validate answers
        party_questions = get_personalized_questions(party)
        questions_dict = {q['id']: q for q in party_questions}
        
        # Validate answers and calculate points
        total_points_earned = 0
        correct_count = 0
        question_results = []
        
        for answer_data in answers:
            question_id = answer_data.get('question_id')
            user_answer = answer_data.get('answer')
            
            if question_id not in questions_dict:
                continue
            
            question = questions_dict[question_id]
            is_correct = user_answer == question['correct_answer']
            
            if is_correct:
                total_points_earned += question['points']
                correct_count += 1
            
            question_results.append({
                'question_id': question_id,
                'question': question['question'],
                'your_answer': user_answer,
                'correct_answer': question['correct_answer'],
                'is_correct': is_correct,
                'points_earned': question['points'] if is_correct else 0
            })
        
        # Update game score
        score.total_points += total_points_earned
        score.level = score.calculate_level()
        score.save()
        
        return Response({
            'party': {
                'id': party.id,
                'name': party.name
            },
            'results': {
                'total_questions': len(question_results),
                'correct_answers': correct_count,
                'points_earned': total_points_earned,
                'accuracy': round((correct_count / len(question_results) * 100), 1) if question_results else 0
            },
            'question_results': question_results,
            'score': {
                'id': score.id,
                'total_points': score.total_points,
                'level': score.level,
                'points_earned': total_points_earned
            }
        })
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get list of available trivia categories"""
        categories = list(set(q['category'] for q in TRIVIA_QUESTION_TEMPLATES))
        return Response({
            'categories': categories,
            'total_categories': len(categories)
        })
