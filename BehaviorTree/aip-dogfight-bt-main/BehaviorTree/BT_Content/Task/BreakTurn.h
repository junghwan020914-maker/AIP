#pragma once
/*
	BreakTurn - DBFM(방어) 기동. 위협을 향해 최대선회로 당겨 3-9 라인(beam)으로 밀어내고
	오버슛을 유도한다. 코너속도 유지를 위해 약간 기수 아래로 당긴다.
	VP = 내위치 + 전방*a + (적방향 좌우)*b - 아래*c
*/
#include "../../behaviortree_cpp_v3\action_node.h"
#include "../../behaviortree_cpp_v3/bt_factory.h"
#include "../../../Geometry/Vector3.h"
#include "../Functions.h"
#include "../BlackBoard/CPPBlackBoard.h"
using namespace BT;
namespace Action
{
	class BreakTurn : public SyncActionNode
	{
	public:
		BreakTurn(const std::string& name, const NodeConfiguration& config) : SyncActionNode(name, config) {}
		~BreakTurn() {}
		static PortsList providedPorts();
		NodeStatus tick() override;
	};
}
